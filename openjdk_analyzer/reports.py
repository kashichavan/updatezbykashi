"""
CSV and JSON Index Report Generator per requirements #7, #8, #9.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    import csv
    HAS_PANDAS = False
from openjdk_analyzer.metadata import JavaFileMetadata


class ReportGenerator:
    """Generates dataset_index.json, summary statistics, and CSV reports."""

    def generate_all(self, metadata_list: List[JavaFileMetadata], output_dir: Union[str, Path]):
        """Generates dataset_index.json, CSV report, and console/summary statistics."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        self._generate_dataset_index(metadata_list, out_path / "dataset_index.json")
        self._generate_csv_report(metadata_list, out_path / "dataset_report.csv")
        stats = self.compute_statistics(metadata_list)
        self._save_json(stats, out_path / "dataset_statistics.json")
        return stats

    def _generate_dataset_index(self, metadata_list: List[JavaFileMetadata], index_file: Path):
        """Generates requirement #7 master index: dataset_index.json."""
        data = [meta.to_dict() for meta in metadata_list]
        self._save_json(data, index_file)

    def _generate_csv_report(self, metadata_list: List[JavaFileMetadata], csv_file: Path):
        """Generates requirement #9 CSV report using pandas."""
        records = []
        for meta in metadata_list:
            records.append({
                "filename": meta.filename,
                "relative_path": meta.relative_path,
                "primary_category": meta.categories[0] if meta.categories else "uncategorized",
                "categories": "|".join(meta.categories),
                "java_version": meta.java_version,
                "features": "|".join(meta.features),
                "lines": meta.lines,
                "size_bytes": meta.size,
                "comment_count": meta.comment_count,
                "class_count": len(meta.classes),
                "method_count": len(meta.methods),
                "expected_compile": meta.expected_compile,
                "sha256": meta.sha256
            })
        if HAS_PANDAS:
            df = pd.DataFrame(records)
            df.to_csv(csv_file, index=False)
        else:
            if not records:
                return
            keys = records[0].keys()
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(records)

    def compute_statistics(self, metadata_list: List[JavaFileMetadata]) -> Dict[str, Any]:
        """Computes requirement #8 statistics."""
        if not metadata_list:
            return {"total_files": 0}

        total_files = len(metadata_list)
        total_lines = sum(m.lines for m in metadata_list)
        avg_loc = total_lines / total_files if total_files else 0.0

        # Files per category
        category_counts: Dict[str, int] = {}
        feature_counts: Dict[str, int] = {}
        version_counts: Dict[str, int] = {}

        for meta in metadata_list:
            for cat in meta.categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1

            for feat in meta.features:
                feature_counts[feat] = feature_counts.get(feat, 0) + 1

            ver = meta.java_version
            version_counts[ver] = version_counts.get(ver, 0) + 1

        sorted_by_size = sorted(metadata_list, key=lambda m: m.size, reverse=True)
        largest_files = [{"relative_path": m.relative_path, "size": m.size} for m in sorted_by_size[:10]]
        smallest_files = [{"relative_path": m.relative_path, "size": m.size} for m in sorted_by_size[-10:]]

        return {
            "total_files": total_files,
            "average_loc": round(avg_loc, 2),
            "files_per_category": category_counts,
            "feature_frequency": feature_counts,
            "java_version_distribution": version_counts,
            "largest_files": largest_files,
            "smallest_files": smallest_files
        }

    def _save_json(self, data: Any, file_path: Path):
        """Helper to write data to JSON file formatted nicely."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
