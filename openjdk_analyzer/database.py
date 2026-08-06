"""
SQLite database builder & schema manager per requirement #10.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Union
from openjdk_analyzer.metadata import JavaFileMetadata


class DatabaseManager:
    """Manages creation and indexing of searchable SQLite database."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initializes database tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS java_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    absolute_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL UNIQUE,
                    package TEXT,
                    java_version TEXT,
                    primary_category TEXT,
                    categories TEXT,
                    features TEXT,
                    lines INTEGER,
                    size INTEGER,
                    comment_count INTEGER,
                    classes TEXT,
                    interfaces TEXT,
                    enums TEXT,
                    records TEXT,
                    annotations TEXT,
                    methods TEXT,
                    constructors TEXT,
                    fields TEXT,
                    expected_compile TEXT,
                    sha256 TEXT UNIQUE
                )
            """)

            # Create Indexes for fast querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON java_files(filename);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_primary_category ON java_files(primary_category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sha256 ON java_files(sha256);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lines ON java_files(lines);")
            conn.commit()

    def insert_batch(self, metadata_list: List[JavaFileMetadata]):
        """Inserts a batch of JavaFileMetadata objects into SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            records = []
            for meta in metadata_list:
                primary_cat = meta.categories[0] if meta.categories else "uncategorized"
                records.append((
                    meta.filename,
                    meta.absolute_path,
                    meta.relative_path,
                    meta.package,
                    meta.java_version,
                    primary_cat,
                    json.dumps(meta.categories),
                    json.dumps(meta.features),
                    meta.lines,
                    meta.size,
                    meta.comment_count,
                    json.dumps(meta.classes),
                    json.dumps(meta.interfaces),
                    json.dumps(meta.enums),
                    json.dumps(meta.records),
                    json.dumps(meta.annotations),
                    json.dumps(meta.methods),
                    json.dumps(meta.constructors),
                    json.dumps(meta.fields),
                    meta.expected_compile,
                    meta.sha256
                ))

            cursor.executemany("""
                INSERT OR REPLACE INTO java_files (
                    filename, absolute_path, relative_path, package, java_version,
                    primary_category, categories, features, lines, size, comment_count,
                    classes, interfaces, enums, records, annotations, methods, constructors,
                    fields, expected_compile, sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()
