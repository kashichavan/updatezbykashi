"""
Multi-label Java file classifier.
Categorizes files into target folders per requirement #5.
"""

from typing import List
from openjdk_analyzer.metadata import JavaFileMetadata


class JavaFileClassifier:
    """Classifies Java files into target functional and test categories."""

    def classify(self, meta: JavaFileMetadata) -> List[str]:
        """
        Determines applicable categories for a Java source file based on features,
        package names, imports, and symbol contents.
        Spec #5 target folders:
        valid, syntax, semantic, runtime, parser, lexer, annotations,
        generics, lambda, records, modules, collections, concurrency, io, advanced
        """
        categories: List[str] = []

        # 1. Direct Feature-Based Mapping
        if "annotations" in meta.features or meta.annotations:
            categories.append("annotations")
        if "generics" in meta.features or "wildcards" in meta.features:
            categories.append("generics")
        if "lambdas" in meta.features or "streams" in meta.features:
            categories.append("lambda")
        if "records" in meta.features or meta.records:
            categories.append("records")
        if "modules" in meta.features or "module-info.java" in meta.filename:
            categories.append("modules")
        if "threads" in meta.features or "synchronized" in meta.features or "virtual threads" in meta.features:
            categories.append("concurrency")

        # 2. Package / Import Based Mapping
        import_str = " ".join(meta.imports).lower()
        if "java.util.concurrent" in import_str:
            if "concurrency" not in categories:
                categories.append("concurrency")
        if "java.util" in import_str or "collections" in meta.relative_path.lower():
            categories.append("collections")
        if "java.io" in import_str or "java.nio" in import_str or "io" in meta.relative_path.lower():
            categories.append("io")

        # 3. Compiler Component / Test Suite Mapping
        rel_path_lower = meta.relative_path.lower()
        if "parser" in rel_path_lower or "parse" in rel_path_lower:
            categories.append("parser")
        if "lexer" in rel_path_lower or "scan" in rel_path_lower or "token" in rel_path_lower:
            categories.append("lexer")
        if "type" in rel_path_lower or "check" in rel_path_lower or "attr" in rel_path_lower:
            categories.append("semantic")
        if "syntax" in rel_path_lower or "grammar" in rel_path_lower:
            categories.append("syntax")

        # 4. Advanced Language Constructs
        if any(f in meta.features for f in ["sealed classes", "pattern matching", "text blocks", "preview features", "reflection"]):
            categories.append("advanced")

        # 5. Compile Expectation & Fallbacks
        if meta.expected_compile == "fail":
            if "syntax" not in categories and "semantic" not in categories:
                categories.append("syntax")
        else:
            categories.append("valid")
            categories.append("runtime")

        # Ensure every file has at least one valid primary category
        if not categories:
            categories.append("valid")

        return sorted(list(set(categories)))
