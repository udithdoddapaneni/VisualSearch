"""Implement a logging server that runs on a port.

The server receives log info from various other processes,
logging them into a single file.
"""

# GiG

import argparse
from pathlib import Path

import zmq
from config_types import LoggingConfigs
from loguru import logger

# This file implements a logging server that runs in a port
# and that recieves log info from various other processes
# and then logs them into a single file


# Copied from https://loguru.readthedocs.io/en/stable/resources/recipes.html#sending-and-receiving-log-messages-across-network-or-processes


def set_logging_configs(logging_configs: LoggingConfigs) -> None:
    """Configure the logger with the provided logging configurations.

    Args:
        logging_configs (LoggingConfigs): The logging configurations to use.

    """
    # remove the previous settings so that it does not print in stderr and only to file
    logger.remove()

    # Add shared file logger
    logger.add(
        logging_configs.log_file_name,
        rotation=logging_configs.log_rotation,  # Rotate at 00:00
        compression=logging_configs.log_compression,  # Compress rotated files
        format=logging_configs.server_log_format,
        level=logging_configs.min_log_level,
        enqueue=True,  # Thread-safe logging
        backtrace=True,  # Detailed error traces
        diagnose=True,  # Enable exception diagnostics
    )


def start_logging_server(logging_configs: LoggingConfigs) -> None:
    """Start the logging server."""
    socket = zmq.Context().socket(zmq.SUB)
    socket.bind(f"tcp://127.0.0.1:{logging_configs.log_server_port}")
    socket.subscribe("")

    while True:
        try:
            ret_val = socket.recv_multipart()
            log_level_name, message = ret_val

            log_level_name = log_level_name.decode("utf8").strip()
            message = message.decode("utf8").strip()

            logger.log(log_level_name, message)

        except Exception:  # noqa: BLE001
            logger.exception("Got an exception when logging: ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file_path")
    args = parser.parse_args()

    CONFIG_FILE_NAME = Path(args.config_file_path)
    logging_configs = LoggingConfigs.load_from_path(CONFIG_FILE_NAME)
    set_logging_configs(logging_configs)
    start_logging_server(logging_configs)
