"""
Main CLI entry point for OpenJDK Test Suite Miner & Categorizer Tool.
Integrates multiprocessing, tqdm progress bar, metadata JSON generation, DB indexing, and CSV reports.
"""

import json
import shutil
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Union
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, total=None, desc=""):
        return iterable

from openjdk_analyzer.scanner import OpenJDKScanner
from openjdk_analyzer.analyzer import JavaFileAnalyzer
from openjdk_analyzer.classifier import JavaFileClassifier
from openjdk_analyzer.metadata import JavaFileMetadata
from openjdk_analyzer.database import DatabaseManager
from openjdk_analyzer.reports import ReportGenerator
from openjdk_analyzer.utils import setup_logger

logger = setup_logger()


def process_file_worker(args: Tuple[str, str, str]) -> JavaFileMetadata:
    """Worker function for multiprocessing execution."""
    file_path_str, sha256_hash, repo_root_str = args
    file_path = Path(file_path_str)
    repo_root = Path(repo_root_str)

    analyzer = JavaFileAnalyzer()
    classifier = JavaFileClassifier()

    meta = analyzer.analyze(file_path, sha256_hash, repo_root)
    meta.categories = classifier.classify(meta)
    return meta


def copy_file_to_dataset(meta: JavaFileMetadata, dataset_dir: Path):
    """Copies Java file and metadata.json into categorized dataset directory while preserving path hierarchy."""
    primary_category = meta.categories[0] if meta.categories else "uncategorized"
    target_folder = dataset_dir / primary_category / Path(meta.relative_path).parent
    target_folder.mkdir(parents=True, exist_ok=True)

    target_java = target_folder / meta.filename
    try:
        shutil.copy2(meta.absolute_path, target_java)
        meta_json_file = target_folder / f"{meta.filename}.metadata.json"
        with open(meta_json_file, "w", encoding="utf-8") as f:
            json.dump(meta.to_dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Error copying file {meta.relative_path}: {e}")


def run_pipeline(repo_root: Union[str, Path], output_dir: Union[str, Path], max_workers: int = 4):
    """Runs full extraction, classification, database creation, and report generation pipeline."""
    repo_root = Path(repo_root).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting OpenJDK Analysis Pipeline on: {repo_root}")
    logger.info(f"Output Directory: {output_dir}")

    # 1. Scan Repository
    scanner = OpenJDKScanner(repo_root)
    scanned_files = scanner.scan()

    if not scanned_files:
        logger.warning("No Java files found to process.")
        return

    # 2. Multiprocessing Extraction & Classification
    worker_tasks = [(str(file_path), sha256_hash, str(repo_root)) for file_path, sha256_hash in scanned_files]
    metadata_results: List[JavaFileMetadata] = []

    logger.info("Analyzing and classifying Java test files using multiprocessing...")
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file_worker, task) for task in worker_tasks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Java Files"):
            try:
                meta = future.result()
                metadata_results.append(meta)
            except Exception as e:
                logger.error(f"Error processing worker task: {e}")

    # 3. Copy files to categorized dataset directory
    dataset_dir = output_dir / "dataset"
    logger.info("Copying files to categorized dataset directory...")
    for meta in tqdm(metadata_results, desc="Structuring Categorized Dataset"):
        copy_file_to_dataset(meta, dataset_dir)

    # 4. Insert into SQLite Database
    db_path = output_dir / "openjdk_dataset.db"
    logger.info(f"Populating SQLite Database: {db_path}")
    db_manager = DatabaseManager(db_path)
    db_manager.insert_batch(metadata_results)

    # 5. Generate Index & Reports
    logger.info("Generating CSV reports and dataset index...")
    report_gen = ReportGenerator()
    stats = report_gen.generate_all(metadata_results, output_dir)

    logger.info("=" * 60)
    logger.info(" ANALYSIS PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info(f" Total Files Analyzed: {stats['total_files']}")
    logger.info(f" Average Lines of Code: {stats['average_loc']}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="OpenJDK Test Suite Miner & Categorizer Tool")
    parser.add_argument("--repo-root", required=True, help="Path to OpenJDK repository root directory")
    parser.add_argument("--output-dir", default="openjdk_dataset_output", help="Directory to save output dataset, DB, and reports")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel worker processes")

    args = parser.parse_args()
    run_pipeline(args.repo_root, args.output_dir, args.workers)


if __name__ == "__main__":
    main()
