"""
Utility functions for hashing, path processing, and logging.
"""

import hashlib
import logging
from pathlib import Path
from typing import Union


def setup_logger(log_file: Union[str, Path] = "openjdk_analyzer.log", level=logging.INFO) -> logging.Logger:
    """Configures and returns a thread-safe logger."""
    logger = logging.getLogger("OpenJDKAnalyzer")
    logger.setLevel(level)

    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(level)
        fh_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

        # Stream handler
        sh = logging.StreamHandler()
        sh.setLevel(logging.WARNING)
        sh_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        sh.setFormatter(sh_formatter)
        logger.addHandler(sh)

    return logger


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """Computes SHA-256 hash of a file for exact deduplication."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()
