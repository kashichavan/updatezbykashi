# OpenJDK Test Suite Miner & Categorizer Tool

## Project Structure
```text
openjdk_analyzer/
├── __init__.py
├── utils.py          # File hashing, logging, path utilities
├── metadata.py       # Dataclasses & Metadata JSON generator schema
├── scanner.py        # Recursive OpenJDK repo scanner with SHA-256 deduplication
├── analyzer.py       # High-performance Java AST & regex feature extraction engine
├── classifier.py     # Multi-label category classifier rules
├── database.py       # Searchable SQLite database builder & schema manager
├── reports.py        # Pandas CSV reports & JSON dataset index builder
├── main.py           # CLI entry point with Multiprocessing & tqdm progress bar
└── tests/            # Comprehensive PyTest unit tests
    ├── __init__.py
    ├── test_analyzer.py
    ├── test_classifier.py
    └── test_database.py
```
