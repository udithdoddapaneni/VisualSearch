"""The module starts the logging server with configurations from logging_config.toml."""

import argparse
from pathlib import Path

from config_types import LoggingConfigs
from logging_server import set_logging_configs, start_logging_server


def main() -> None:
    """Start the logging server with configurations from the provided config file."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file_path", default="logging_config.toml")
    args = parser.parse_args()

    config_file_name = Path(args.config_file_path)

    if not config_file_name.exists():
        msg = f"Config file {config_file_name} not found"
        raise FileNotFoundError(msg)

    logging_configs = LoggingConfigs.load_from_path(config_file_name)

    # Create logs directory if it doesn't exist
    log_dir = Path(logging_configs.log_file_name).parent
    log_dir.mkdir(exist_ok=True)

    set_logging_configs(logging_configs)
    start_logging_server(logging_configs)


if __name__ == "__main__":
    main()
