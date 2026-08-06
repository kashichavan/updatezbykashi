"""
Recursive OpenJDK test suite scanner with SHA-256 deduplication and path filtering.
"""

from pathlib import Path
from typing import List, Set, Tuple, Union
from openjdk_analyzer.utils import calculate_sha256, setup_logger

logger = setup_logger()

# Target OpenJDK directories per spec #2
TARGET_DIRS = [
    Path("test/langtools"),
    Path("test/jdk"),
    Path("test/hotspot")
]


class OpenJDKScanner:
    """Scans OpenJDK repository for Java test files, skipping duplicate SHA-256 content."""

    def __init__(self, repo_root: Union[str, Path]):
        self.repo_root = Path(repo_root).resolve()
        self.seen_hashes: Set[str] = set()

    def scan(self) -> List[Tuple[Path, str]]:
        """
        Recursively locates Java source files in target directories.
        Returns list of (absolute_file_path, sha256_hash).
        """
        collected_files: List[Tuple[Path, str]] = []

        if not self.repo_root.exists():
            logger.error(f"Repository root directory does not exist: {self.repo_root}")
            return collected_files

        # Identify directories to scan
        scan_paths = []
        for rel_target in TARGET_DIRS:
            target_path = self.repo_root / rel_target
            if target_path.exists():
                scan_paths.append(target_path)

        # Fallback to scanning whole root if specific subdirs don't exist
        if not scan_paths:
            scan_paths = [self.repo_root]

        for scan_path in scan_paths:
            logger.info(f"Scanning directory: {scan_path}")
            for java_file in scan_path.rglob("*.java"):
                if not java_file.is_file():
                    continue

                try:
                    file_hash = calculate_sha256(java_file)
                    if file_hash in self.seen_hashes:
                        logger.info(f"Skipping duplicate file (SHA-256 match): {java_file}")
                        continue

                    self.seen_hashes.add(file_hash)
                    collected_files.append((java_file, file_hash))
                except Exception as e:
                    logger.error(f"Error reading {java_file}: {e}")

        logger.info(f"Scanned total {len(collected_files)} unique Java source files.")
        return collected_files
