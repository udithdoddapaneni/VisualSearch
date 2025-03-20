# System Architecture Overview

## High-Level Architecture

ViZearch is built using a modular architecture that separates concerns and allows for scalability and maintainability. The system consists of four main components:

```mermaid
graph TD
    %% Main components with clear labeling
    UI[Frontend UI] --> API[REST API]
    API --> Search[Tantivy Indexer]
    API --> Media[Media Processor]
    
    %% Media processing components
    Media --> BLIP[BLIP Model]
    BLIP --> Vector[Captions]
    Vector --> Search
    
    %% Metadata components
    Media --> EXIF[EXIF Extractor]
    EXIF --> Search
    
    %% Styling for better visibility
    classDef blue fill:#bbdefb,stroke:#1976d2,stroke-width:1px
    classDef green fill:#c8e6c9,stroke:#388e3c,stroke-width:1px
    
    class UI,API blue
    class Search,Media,BLIP,Vector,EXIF,Temporal green
```

## Core Components

### 1. Frontend
A React-based user interface that provides:

- Search interface with query input
- Results display with media previews
- Filtering options
- Result management

### 2. API Layer
There two API options:
(See Locust Load Testing)

- Fast API based
- BentoML based

### 3. Media Processing Pipeline
Responsible for:

- Ingesting media files (images and videos)
- Extracting frames from videos
- Preprocessing images for the BLIP model
- Extracting EXIF data

### 4. Semantic Understanding Engine
Built around the BLIP model:

- Processes images to understand visual content
- Generates textual descriptions of visual content

### 5. Tantivy Indexer
Based on Tantivy:

- Maintains indices for fast retrieval
- Performs hybrid search combining semantic and metadata filtering
- Ranks results by relevance




