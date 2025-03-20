"""Searcher API."""

from __future__ import (
    annotations,  # Do not remove !! as it is needed for loguru.Message
)

import asyncio
import io
import os
import shutil
import sys
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import fastapi
import tantivy
import yaml
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from PIL import Image
from request_models import Docs, Query  # noqa: TC002
from utils import ACCEPTED, IMAGES_PATH, VIDEOS_PATH, Blip, image_adder, video_adder

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

if TYPE_CHECKING:
    from fastapi.responses import Response
    from starlette.types import Scope

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

INDEX_PATH = Path("..", "index", "data")
LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")

app = fastapi.FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CachingStaticFiles(StaticFiles):
    """Caaches Static Files."""

    def __init__(self, cache_size:int=128, *args, **kwargs) -> None:
        """Initialize the CachingStaticFiles cache."""
        super().__init__(*args, **kwargs)
        self.cache = OrderedDict()
        self.cachesize = cache_size
    async def get_response(self, path: str, scope:Scope) -> Response:
        """Get cached response."""
        if path in self.cache:
            return self.cache[path]
        response = await super().get_response(path, scope)
        if len(self.cache) >= self.cachesize:
            self.cache.popitem(last=True)
        if response.status_code == ACCEPTED:
            self.cache[path] = response
        return response

app.mount("/images", CachingStaticFiles(directory=IMAGES_PATH, cache_size=128), name="static")
app.mount("/videos", CachingStaticFiles(directory=VIDEOS_PATH, cache_size=512), name="static")

with Path.open(Path("..", "config.yaml")) as config_file:
    CONFIG = yaml.safe_load(config_file)

# Setup logging
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(LOGGING_CONFIG_PATH)
    setup_network_logger_client(logging_configs, logger)

MODEL = Blip(config=CONFIG)


class GlobalVariables:
    """Store Global Variables."""

    index: tantivy.Index | None = None


def initialize_index() -> bool:
    """Initialize the search index, optionally rebuilding from scratch."""
    if Path.exists(INDEX_PATH):
        logger.info(f"Removing existing index at {INDEX_PATH}")
        shutil.rmtree(INDEX_PATH)

    if not Path.exists(INDEX_PATH):
        logger.info(f"Creating new index directory at {INDEX_PATH}")
        Path.mkdir(INDEX_PATH, parents=True)

        # Create schema and initialize index
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("caption", stored=True, tokenizer_name="en_stem")
        schema_builder.add_text_field("filename", stored=True)
        schema_builder.add_text_field("type", stored=True)
        schema_builder.add_integer_field("timestamp", stored=True)
        schema = schema_builder.build()
        GlobalVariables.index = tantivy.Index(schema=schema, path=INDEX_PATH.as_posix())
        return True
    # Use existing index
    set_index()
    return False


def startup() -> dict:
    """Reload the images and videos on startup."""
    try:
        initialize_index()
        writer = None
        writer = GlobalVariables.index.writer()
        writer.delete_all_documents()
        writer.commit()
        writer = None
        batch_size = 16
        logger.info("Starting to process images")
        image_adder(add_fn=add_multiple, batch_size=batch_size, model=MODEL)
        logger.info("Starting to process videos")
        video_adder(add_fn=add_multiple, batch_size=batch_size, model=MODEL)
        logger.info("Data loading completed successfully")
    except (Exception, BaseExceptionGroup) as e:
        logger.error(f"Error during startup: {e!s}")
        return {"response": str(e)}
    else:
        return {"response": "okay"}


def set_index() -> None:
    """Reset index."""
    GlobalVariables.index = tantivy.Index.open(INDEX_PATH.as_posix())


def add_multiple(docs: Docs) -> None:
    """Add multiple documents into tantivy index."""
    writer = None
    set_index()
    writer = GlobalVariables.index.writer()
    for doc, filename, typ, tstamp in zip(
        docs.texts,
        docs.filenames,
        docs.types,
        docs.timestamps,
        strict=False,
    ):
        writer.add_document(
            tantivy.Document(caption=doc, filename=filename, type=typ, timestamp=tstamp),
        )
    writer.commit()
    writer = None


@app.get("/all_images")
async def all_images() -> dict:
    """Get the filenames of all the images."""
    image_names = []
    for _dirpath, _dirnames, filenames in os.walk(IMAGES_PATH):
        image_names.extend(filenames)
    return {"response": image_names}


@app.get("/all_videos")
async def all_videos() -> dict:
    """Get the filenames of all the videos."""
    image_names = []
    for _dirpath, _dirnames, filenames in os.walk(VIDEOS_PATH):
        image_names.extend(filenames)
    return {"response": image_names}


@lru_cache
@app.post("/query")
async def query(query: Query) -> dict:
    """Make a query."""
    try:
        logger.info(
            f"Processing query: '{query.text}', type: {query.type}, limit: {query.n}",
        )
        set_index()
        searcher = None
        searcher = GlobalVariables.index.searcher()
        try:
            caption_query = GlobalVariables.index.parse_query(query.text, ["caption"])
            type_query = tantivy.Query.term_query(
                schema=GlobalVariables.index.schema,
                field_name="type",
                field_value=query.type,
            )
            parsed_query = tantivy.Query.boolean_query(
                [
                    (tantivy.Occur.Must, caption_query),
                    (tantivy.Occur.Must, type_query),
                ],
            )
        except ValueError as e:
            return {"response": str(e), "results": []}
        results = [
            {
                "filename": searcher.doc(doc)["filename"][0],
                "caption": searcher.doc(doc)["caption"][0],
                "type": searcher.doc(doc)["type"][0],
                "timestamp": searcher.doc(doc)["timestamp"][0],
            }
            for _, doc in searcher.search(parsed_query, limit=query.n).hits
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
        searcher = None
        logger.info(f"Query returned {len(results)} results")

    except (Exception, BaseException) as e:
        logger.exception(f"Query execution error: {e!s}")
        return {"response": str(e), "results": {}}
    else:
        return {"response": "okay", "results": results}

@app.post("/caption")
async def caption(image: UploadFile = File(...)) -> dict:
    """Get the caption of an image."""
    try:
        image_bytes = await image.read()
        image = Image.open(io.BytesIO(image_bytes))
        caption = await asyncio.threads.to_thread(MODEL.generate_captions, [image])
        response = {"response": "okay", "caption": caption}
    except (Exception, BaseException) as e:
        logger.exception(f"Error during captioning: {e!s}")
        return {"response": str(e)}
    else:
        return response

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting the searcher API")
    startup()
    uvicorn.run("__main__:app", **CONFIG["searcher"])
