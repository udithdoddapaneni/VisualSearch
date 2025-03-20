"""Video and Image adders."""

import base64
import os
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import httpx
import numpy as np
from fastapi.exceptions import HTTPException
from moviepy.editor import VideoFileClip
from PIL import Image
from request_models import Docs

VIDEOS_PATH = Path("..", "data", "videos")
IMAGES_PATH = Path("..", "data", "images")
INTERVAL = 5
ACCEPTED = 200


class Blip:
    """Class for calling Blip API."""

    def __init__(self, config: dict) -> None:
        """Store link for API service."""
        self.service = (
            "http://"
            + config["model"]["host"]
            + ":"
            + str(config["model"]["port"])
            + "/generate_captions"
        )

    def encode(self, image: Image.Image) -> str:
        """Convert PIL image to bytes (base64) then to string."""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def raise_http_exception(self, response: httpx.Response) -> None:
        """Raise an HTTPException."""
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    def generate_captions(self, image_list: list[Image.Image]) -> list[str]:
        """Generate captions for the given image."""
        try:
            images = [self.encode(image) for image in image_list]
            response = httpx.post(
                url=self.service,
                json={"images": images},
                timeout=httpx.Timeout(120),
            )
            if response.status_code != ACCEPTED:
                self.raise_http_exception(response)
            return response.json()["captions"]
        except HTTPException:
            return []


def video_adder(add_fn: Callable, batch_size: int, model: Blip) -> None:
    """Get captions for video frames at varying times batch-wise and add them in the tantivy index."""
    for dirpath, _dirnames, filenames in os.walk(VIDEOS_PATH):
        images = []
        fnames = []
        tstamps = []
        modified_times = []
        unique_captions = set()
        for filename in filenames:
            try:
                path = Path(dirpath, filename)
                modified_time = os.path.getmtime(path.as_posix())
                modified_times.append(modified_time)
                video = VideoFileClip(path.as_posix())
                for t in np.arange(0, video.duration, INTERVAL):  # capture every 5 seconds
                    frame = video.get_frame(t)
                    image = Image.fromarray(frame)
                    images.append(image)
                    fnames.append(filename)
                    tstamps.append(t)
                    if len(images) >= batch_size:
                        batch_captions = model.generate_captions(images)
                        documents = (
                            set(zip(batch_captions, fnames, strict=False)) - unique_captions
                        )
                        unique_captions |= documents
                        batch_captions, fnames = map(list, zip(*documents, strict=False))
                        docs = Docs(
                            texts=batch_captions,
                            filenames=fnames,
                            types=["video"] * batch_size,
                            timestamps=tstamps,
                            modified_times=modified_times
                        )
                        add_fn(docs)
                        images = []
                        fnames = []
                        tstamps = []
                        modified_times = []
            except (Exception, BaseException):
                continue
            video.close()
        if len(images) > 0:
            batch_captions = model.generate_captions(images)
            documents = set(zip(batch_captions, fnames, strict=False)) - unique_captions
            unique_captions |= documents
            batch_captions, fnames = map(list, zip(*documents, strict=False))
            docs = Docs(
                texts=batch_captions,
                filenames=fnames,
                types=["video"] * len(batch_captions),
                timestamps=tstamps,
                modified_times=modified_times
            )
            add_fn(docs)


def image_adder(add_fn: Callable, batch_size: int, model: Blip) -> None:
    """Get captions for images batch-wise and add them in the tantivy index."""
    for dirpath, _dirnames, filenames in os.walk(IMAGES_PATH):
        images = []
        fnames = []
        modified_times = []
        for filename in filenames:
            try:
                path = Path(dirpath, filename)
                modified_time = os.path.getmtime(path.as_posix())
                modified_times.append(modified_time)
                image = Image.open(path)
                images.append(image)
                fnames.append(filename)
                if len(images) >= batch_size:
                    batch_captions = model.generate_captions(images)
                    docs = Docs(
                        texts=batch_captions,
                        filenames=fnames,
                        types=["image"] * batch_size,
                        timestamps=[0] * len(batch_captions),
                        modified_times=modified_times
                    )
                    add_fn(docs)
                    images = []
                    fnames=[]
                    modified_times = []
            except (Exception, BaseException):
                continue
        if len(images) > 0:
            batch_captions = model.generate_captions(images)
            docs = Docs(
                texts=batch_captions,
                filenames=fnames,
                types=["image"] * len(batch_captions),
                timestamps=[0] * len(batch_captions),
                modified_times=modified_times
            )
            add_fn(docs)
