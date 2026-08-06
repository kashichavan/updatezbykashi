"""
Standard Library Unittest test suite for openjdk_analyzer package.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from openjdk_analyzer.analyzer import JavaFileAnalyzer
from openjdk_analyzer.classifier import JavaFileClassifier
from openjdk_analyzer.database import DatabaseManager


class TestOpenJDKAnalyzer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

        self.sample_code = """
        package com.example.test;

        import java.util.List;
        import java.util.stream.Stream;

        public sealed class StudentRecord permits HonorsStudent {
            private String name;

            public StudentRecord(String name) {
                this.name = name;
            }

            public String getName() {
                return this.name;
            }
        }

        final class HonorsStudent extends StudentRecord {
            public HonorsStudent(String name) {
                super(name);
            }
        }
        """
        self.sample_file = self.tmp_path / "StudentRecord.java"
        self.sample_file.write_text(self.sample_code, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_java_file_analyzer(self):
        analyzer = JavaFileAnalyzer()
        meta = analyzer.analyze(self.sample_file, "hash123", self.tmp_path)

        self.assertEqual(meta.filename, "StudentRecord.java")
        self.assertEqual(meta.package, "com.example.test")
        self.assertIn("java.util.List", meta.imports)
        self.assertIn("StudentRecord", meta.classes)
        self.assertIn("sealed classes", meta.features)
        self.assertGreater(meta.lines, 10)

    def test_java_file_classifier(self):
        analyzer = JavaFileAnalyzer()
        classifier = JavaFileClassifier()

        meta = analyzer.analyze(self.sample_file, "hash123", self.tmp_path)
        categories = classifier.classify(meta)

        self.assertTrue("valid" in categories or "advanced" in categories)

    def test_database_manager(self):
        db_file = self.tmp_path / "test.db"
        db = DatabaseManager(db_file)

        analyzer = JavaFileAnalyzer()
        classifier = JavaFileClassifier()

        meta = analyzer.analyze(self.sample_file, "hash123", self.tmp_path)
        meta.categories = classifier.classify(meta)

        db.insert_batch([meta])
        self.assertTrue(db_file.exists())


if __name__ == "__main__":
    unittest.main()
