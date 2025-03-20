"""API service served using bentoml."""
from __future__ import annotations

import base64
import os
import shutil
from io import BytesIO
from pathlib import Path
from typing import Literal

import tantivy
import torch
from moviepy.editor import VideoFileClip
from PIL import Image
from pydantic import BaseModel, Field
from transformers import BlipForConditionalGeneration, BlipProcessor

import bentoml

# ---------------------------
# Helper Models and Functions
# ---------------------------


class Images(BaseModel):
    """Stores base64 encoded image strings."""

    images: list[str]


def decode_images(images: list[str]) -> list[Image.Image]:
    """Decode the image strings to list of pillow images."""
    pil_images = []
    for img_str in images:
        image_str = img_str
        if image_str.startswith("data:image"):
            image_str = image_str.split(",")[1]
        missing_padding = len(image_str) % 4
        if missing_padding:
            image_str += "=" * (4 - missing_padding)
        try:
            img_bytes = base64.b64decode(image_str)
            img = Image.open(BytesIO(img_bytes))
            pil_images.append(img)
        except (Exception, BaseException) as e:
            error = "Invalid Base64 image format"
            raise ValueError(error) from e
    return pil_images


class Query(BaseModel):
    """Query Class for search."""

    text: str = Field(default="", description="Search text")
    type: Literal["image", "video"] = "image"
    n: int = Field(default=10, gt=0, description="Number of results to return")


class Docs(BaseModel):
    """Documents Class."""

    texts: list[str] = Field(default=[], description="Document texts")
    filenames: list[str] = Field(default=[], description="Document filenames")
    types: list[str] = Field(default=[], description="Document types")
    timestamps: list[int] = Field(default=[], description="Document timestamps")


# ---------------------------
# Constants and Paths
# ---------------------------

VIDEOS_PATH = Path("..", "..", "data", "videos")
IMAGES_PATH = Path("..", "..", "data", "images")
INDEX_PATH = Path("..","index", "data")

INTERVAL = 5
BATCH_SIZE = 16


# ---------------------------
# Unified BentoML Service
# ---------------------------


@bentoml.service(
    resources={"cpu": "2", "memory": "4Gi"},
    traffic={"timeout": 60},
    http={
        "cors": {
            "enabled": True,
            "access_control_allow_origins": ["*"],
            "access_control_allow_methods": ["GET", "OPTIONS", "POST", "HEAD", "PUT"],
            "access_control_allow_credentials": True,
            "access_control_allow_headers": ["*"],
            "access_control_max_age": 1200,
            "access_control_expose_headers": ["Content-Length"],
        },
    },
)
class BlipTantivyService:
    """Class for Blip-Tantivy API service."""

    def __init__(self) -> None:
        """Initialize the Blip-Tantivy Service."""
        self.model_path = "Salesforce/blip-image-captioning-base"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = BlipProcessor.from_pretrained(self.model_path)

        try:
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_path).to(self.device)
        except (Exception, BaseException):
            self.device = "cpu"
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_path)

        VIDEOS_PATH.mkdir(parents=True, exist_ok=True)
        IMAGES_PATH.mkdir(parents=True, exist_ok=True)

        if INDEX_PATH.exists():
            shutil.rmtree(INDEX_PATH.as_posix())
        if not INDEX_PATH.exists():
            INDEX_PATH.mkdir(parents=True)
            schema_builder = tantivy.SchemaBuilder()
            schema_builder.add_text_field("caption", stored=True, tokenizer_name="en_stem")
            schema_builder.add_text_field("filename", stored=True)
            schema_builder.add_text_field("type", stored=True)
            schema_builder.add_integer_field("timestamp", stored=True)
            schema = schema_builder.build()
            self.index = tantivy.Index(schema=schema, path=INDEX_PATH.as_posix())

        writer = self.index.writer()
        writer.commit()
        writer = None
        self.startup()

    def _generate_captions_from_images(self, images: list[Image.Image]) -> list[str]:
        """Generate captions for a list of images."""
        inputs = self.processor(images, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs)
        return self.processor.batch_decode(outputs, skip_special_tokens=True)

    def generate_captions(self, batch: Images) -> dict:
        """Generate captions for the batch."""
        images = decode_images(batch.images)
        captions = self._generate_captions_from_images(images)
        return {"response": "okay", "captions": captions}

    def _reset_index(self) -> None:
        """Reload the index from the index path."""
        try:
            self.index = tantivy.Index.open(INDEX_PATH.as_posix())
        except (Exception, BaseException) as e:
            print(f"Warning: Could not reset index: {e}")

    def add_multiple(self, docs: Docs) -> dict:
        """Add multiple documents to the Tantivy index."""
        print("adding documents")
        try:
            # Create NEW writer for each batch
            writer = self.index.writer()
            for doc, filename, typ, tstamp in zip(
                docs.texts, docs.filenames, docs.types, docs.timestamps, strict=False,
            ):
                if doc:
                    writer.add_document(tantivy.Document(caption=doc, filename=filename, type=typ, timestamp=tstamp))
            writer.commit()
            writer = None  # Critical: Release writer immediately
            result = {"response": "okay"}
        except (Exception, BaseException) as e:
            print(f"Error adding documents: {e}")
            return {"response": f"error: {e}"}
        else:
            return result

    def process_video(self, filename: str) -> None:
        """Generate captions for a video and load them into tantivy."""
        print(f"Starting video processing: {filename}")
        path = VIDEOS_PATH / filename
        try:
            video = VideoFileClip(path.as_posix())
            images = []
            timestamps = []

            for t in range(0, int(video.duration), INTERVAL):
                frame = video.get_frame(t)
                images.append(Image.fromarray(frame))
                timestamps.append(t)

                if len(images) >= BATCH_SIZE:
                    captions = self._generate_captions_from_images(images)
                    docs = Docs(
                        texts=captions,
                        filenames=[filename] * len(captions),
                        types=["video"] * len(captions),
                        timestamps=timestamps,
                    )
                    self.add_multiple(docs)
                    images = []
                    timestamps = []

            if images:
                captions = self._generate_captions_from_images(images)
                docs = Docs(
                    texts=captions,
                    filenames=[filename] * len(captions),
                    types=["video"] * len(captions),
                    timestamps=timestamps,
                )
                self.add_multiple(docs)

            video.close()
            print(f"Successfully processed video: {filename}")
        except (Exception, BaseException) as e:
            print(f"Error processing video {filename}: {e}")

    def process_image(self, filename: str) -> None:
        """Generate caption for an image and load it into tantivy."""
        print(f"Processing image: {filename}")
        path = IMAGES_PATH / filename
        try:
            image = Image.open(path)
            captions = self._generate_captions_from_images([image])
            if captions and captions[0]:
                docs = Docs(texts=[captions[0]], filenames=[filename], types=["image"], timestamps=[0])
                self.add_multiple(docs)
                print(f"Successfully processed image: {filename}")
        except (Exception, BaseException) as e:
            print(f"Error processing image {filename}: {e}")

    def startup(self) -> dict:
        """Load into the tantivy."""
        print("Starting initialization...")
        try:
            writer = self.index.writer()
            writer.delete_all_documents()
            writer.commit()
            writer = None
            print("Index cleared")

            print("Processing images...")
            image_count = 0
            for _dirpath, _, filenames in os.walk(IMAGES_PATH):
                for filename in filenames:
                    print(f"Processing image: {filename}")
                    self.process_image(filename)
                    image_count += 1
            print(f"Processed {image_count} images")

            print("Processing videos...")
            video_count = 0
            for _dirpath, _, filenames in os.walk(VIDEOS_PATH):
                for filename in filenames:
                    print(f"Processing video: {filename}")
                    self.process_video(filename)
                    video_count += 1
            print(f"Processed {video_count} videos")

            response = {"response": "okay"}
        except (Exception, BaseException) as e:
            print(f"Startup error: {e}")
            return {"response": f"error: {e}"}
        else:
            return response

    @bentoml.api(route="/all_images")
    async def all_images(self) -> dict:
        """Get names of all the images."""
        image_names = []
        for _, _, filenames in os.walk(IMAGES_PATH):
            image_names.extend(filenames)
        return {"response": image_names}

    @bentoml.api(route="/all_videos")
    async def all_videos(self) -> dict:
        """Get names of all the videos."""
        video_names = []
        for _, _, filenames in os.walk(VIDEOS_PATH):
            video_names.extend(filenames)
        return {"response": video_names}

    @bentoml.api(route="/query")
    async def query(self, text:str="", type:str="image", n:int=10) -> dict:
        """Make a query."""
        try:
            self._reset_index()
            searcher = self.index.searcher()
            caption_query = self.index.parse_query(text, ["caption"])
            type_query = tantivy.Query.term_query(
                field_name="type",
                field_value=type,
                schema=self.index.schema,
            )
            parsed_query = tantivy.Query.boolean_query(
                [
                    (tantivy.Occur.Must, caption_query),
                    (tantivy.Occur.Must, type_query),
                ],
            )
            results = [
                {
                    "filename":searcher.doc(doc)["filename"][0],
                    "caption": searcher.doc(doc)["caption"][0],
                    "type": searcher.doc(doc)["type"][0],
                    "timestamp": searcher.doc(doc)["timestamp"][0],
                }
                for _, doc in searcher.search(parsed_query, limit=n).hits
            ]
            unique = {
                (result["filename"], result["caption"], result["type"], result["timestamp"]) for result in results
            }
            results = [
                {
                    "filename":result[0],
                    "caption":result[1],
                    "type":result[2],
                    "timestamp":result[3],
                }
                for result in unique
            ]
            response = {"response": "okay", "results": results}
        except (Exception, BaseException) as e:
            return {"response": str(e), "results": {}}
        else:
            return response

    def process_file(self, filename: str, file_type: Literal["image", "video"]) -> dict:
        """Process file."""
        print(f"Processing {file_type}: {filename}")
        if file_type == "image":
            self.process_image(filename)
        elif file_type == "video":
            self.process_video(filename)
        return {"response": "okay"}
