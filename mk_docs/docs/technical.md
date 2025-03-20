# Semantic Search Project Documentation

## Overview

This project is organized into three main folders: `model`, `searcher`, and `unified_logging`. Each folder contains specific modules and scripts that contribute to the overall functionality of the Semantic Search system.

## Folder Structure

### `model`

This folder contains the following files and subdirectories:

- `__init__.py`: Initializes the module.
- `request_models.py`: Contains request models for the application.
- `VLM.py`: Contains the implementation of the Vision-Language Model (VLM).
- `__pycache__/`: Contains cached bytecode files.

### `searcher`

This folder contains the following files and subdirectories:

- `__init__.py`: Initializes the module.
- `BM25.py`: Implements the BM25 search algorithm and the FastAPI application.
- `request_models.py`: Contains request models for the searcher.
- `utils.py`: Contains utility functions and constants.
- `__pycache__/`: Contains cached bytecode files.

### `unified_logging`

This folder contains the following files and subdirectories:

- `__init__.py`: Initializes the module.
- `config_types.py`: Defines configuration types for logging.
- `logging_client.py`: Sets up the logging client.
- `logging_config.toml`: Configuration file for logging settings.
- `logging_server.py`: Implements the logging server.
- `start_logging_server.py`: Script to start the logging server.
- `__pycache__/`: Contains cached bytecode files.
- `logs/`: Directory for storing log files.

## Code Overview

### `searcher/BM25.py`

This file implements the BM25 search algorithm and sets up a FastAPI application. Key components include:

- **Imports**: Various modules and packages are imported, including `fastapi`, `tantivy`, `yaml`, and `loguru`.
- **Constants**: Paths for the index and logging configuration are defined.
- **FastAPI Application**: The FastAPI application is initialized and middleware is added.
- **Static Files**: Static files for images and videos are served using `CachingStaticFiles`.
- **Configuration**: Configuration is loaded from a YAML file.
- **Logging**: Logging is set up using configurations from `logging_config.toml`.
- **Model Initialization**: The `Blip` model is initialized with the loaded configuration.
- **Global Variables**: A class to store global variables is defined.
- **Index Initialization**: A function to initialize the index is defined.

### `unified_logging/logging_config.toml`

This file contains the logging configuration settings:

- **min_log_level**: Minimum log level (e.g., DEBUG).
- **log_server_port**: Port for the log server.
- **client_log_format**: Format for client logs.
- **server_log_format**: Format for server logs.
- **log_rotation**: Log rotation schedule.
- **log_file_name**: Name of the log file.
- **log_compression**: Compression method for logs.
