"""VLM API."""

import sys
from pathlib import Path

import fastapi
import torch
import uvicorn
import yaml
from loguru import logger
from request_models import Images, decode_images
from transformers import BlipForConditionalGeneration, BlipProcessor

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from unified_logging.config_types import LoggingConfigs  # noqa: E402
from unified_logging.logging_client import setup_network_logger_client  # noqa: E402

app = fastapi.FastAPI()

with Path.open(Path("..", "API_KEY.yaml")) as file:
    config = yaml.safe_load(file)
    HF_TOKEN = config["HF_TOKEN"]

with Path.open(Path("..", "config.yaml")) as config_file:
    CONFIG = yaml.safe_load(config_file)

LOGGING_CONFIG_PATH = Path("..", "unified_logging/logging_config.toml")
if LOGGING_CONFIG_PATH.exists():
    logging_configs = LoggingConfigs.load_from_path(LOGGING_CONFIG_PATH)
    setup_network_logger_client(logging_configs, logger)
    logger.info("VLM service started with unified logging")


class Blip:
    """Class for BLIP Model."""

    def __init__(self) -> None:
        """Load the model into appropriate device."""
        logger.info("Initializing BLIP model")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        logger.info("Loading BLIP processor")
        self.processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            token=HF_TOKEN,
        )
        logger.info("Loading BLIP model")
        try:
            # if torch._C._cuda_getDeviceCount() > 0:
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                self.model = BlipForConditionalGeneration.from_pretrained(
                    "Salesforce/blip-image-captioning-base",
                    token=HF_TOKEN,
                ).to(self.device)
            else:
                self.device = "cpu"
                self.model = BlipForConditionalGeneration.from_pretrained(
                    "Salesforce/blip-image-captioning-base",
                    token=HF_TOKEN,
                )
            logger.info("BLIP model loaded successfully")
        except BaseExceptionGroup:
            self.device = "cpu"
            self.model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base",
                token=HF_TOKEN,
            )  # if not enough vram
            logger.info("BLIP model loaded successfully")


captioning_model = Blip()


@app.post("/generate_captions")
async def generate_captions(batch: Images) -> dict:
    """Generate captions for the batch of images."""
    logger.info(f"Received request to generate captions for {len(batch.images)} images")

    images = decode_images(batch.images)
    logger.debug("Images decoded successfully")

    inputs = captioning_model.processor(images, return_tensors="pt").to(
        captioning_model.device,
    )
    logger.debug("Processing images through BLIP processor")

    outputs = captioning_model.model.generate(**inputs)
    logger.debug("Generated caption outputs")

    captions = captioning_model.processor.batch_decode(outputs, skip_special_tokens=True)
    logger.info(f"Generated {len(captions)} captions successfully")

    return {"response": "okay", "captions": captions}


if __name__ == "__main__":
    uvicorn.run("__main__:app", **CONFIG["model"])
