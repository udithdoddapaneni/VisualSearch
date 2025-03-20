# About Our Semantic Search Project

## Learnings
We got more familiar with logging practices and tried to reduce ruff errors. We also got to experiment with other tools like BentoML, Ray Serve , locust etc.


## What We Managed to Accomplish

We significantly improved the performance of our system:

- Enhanced FastAPI response times by parallelizing batch-wise data transmission to the model API
- Improved Tantivy searcher performance by implementing multiple workers
- Successfully addressed initial speed bottlenecks in our system

## Challenges We Faced

Our primary challenges were related to Tantivy implementation:

- Limited documentation and examples for Tantivy's Python implementation
- Encountered numerous bugs that required investigation
- Had to reference the original Rust implementation to understand proper usage patterns
- Time constraints forced us to focus primarily on Tantivy issues

At the End, the addition of EXIF features breaked our system and due to limitation of time, we were forced to remove the feature.

## Limitations and Future Plans

Due to the challenges with Tantivy:

- Our BentoML server currently performs worse than our FastAPI server
- For future assignments, we plan to start with BentoML/Ray integration from the beginning
- We aim to create a more balanced approach to all components in upcoming work
- We will try to re-add the EXIF feature