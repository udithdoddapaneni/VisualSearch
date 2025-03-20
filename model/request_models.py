"""Pydantic models for VLM."""

import base64
from io import BytesIO

from loguru import logger
from PIL import Image
from pydantic import BaseModel


class Images(BaseModel):
    """Image class which stores base64 encoded image strings."""

    images: list[str]


def decode_images(images: Images) -> list[Image.Image]:
    """Convert Base64 strings to PIL Images."""
    pil_images = []
    for img_str in images:
        try:
            img_bytes = base64.b64decode(img_str)
            img = Image.open(BytesIO(img_bytes))
            pil_images.append(img)
        except (Exception, BaseExceptionGroup):
            logger.error(f"Error decoding image: {img_str}")
    return pil_images
