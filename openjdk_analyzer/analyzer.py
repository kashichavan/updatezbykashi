"""
Java AST & Regex feature extraction engine.
Parses Java source files to collect symbols, version metadata, comments, and language features.
"""

import re
from pathlib import Path
from typing import List, Set, Union
from openjdk_analyzer.metadata import JavaFileMetadata


class JavaFileAnalyzer:
    """Analyzes a Java file content to extract metadata, features, and symbols."""

    # Regex patterns for Java language constructs
    RE_PACKAGE = re.compile(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;", re.MULTILINE)
    RE_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([a-zA-Z0-9_.*]+)\s*;", re.MULTILINE)

    # Declarations
    RE_CLASS = re.compile(r"\b(?:public|protected|private|static|final|abstract|sealed|non-sealed)?\s*class\s+([a-zA-Z0-9_$]+)", re.MULTILINE)
    RE_INTERFACE = re.compile(r"\b(?:public|protected|private|static|sealed|non-sealed)?\s*interface\s+([a-zA-Z0-9_$]+)", re.MULTILINE)
    RE_ENUM = re.compile(r"\b(?:public|protected|private|static)?\s*enum\s+([a-zA-Z0-9_$]+)", re.MULTILINE)
    RE_RECORD = re.compile(r"\b(?:public|protected|private|static|final)?\s*record\s+([a-zA-Z0-9_$]+)", re.MULTILINE)
    RE_ANNOTATION_DEF = re.compile(r"\b@interface\s+([a-zA-Z0-9_$]+)", re.MULTILINE)

    # Features
    RE_SEALED = re.compile(r"\b(?:sealed|non-sealed|permits)\b")
    RE_GENERICS = re.compile(r"<[A-Za-z0-9_$,\s\?extends\super]+>")
    RE_WILDCARD = re.compile(r"<\s*\?\s*(?:extends|super)?\s*[^>]*>")
    RE_ARRAY = re.compile(r"\b[a-zA-Z0-9_$]+\s*\[\s*\]")
    RE_LOOPS = re.compile(r"\b(?:for|while|do)\b")
    RE_SWITCH_EXPR = re.compile(r"\bswitch\s*\(.*?\)\s*\{[^}]*->", re.DOTALL)
    RE_PATTERN_MATCHING = re.compile(r"\binstanceof\s+[A-Z][a-zA-Z0-9_$]*\s+[a-z][a-zA-Z0-9_$]*")
    RE_LAMBDAS = re.compile(r"\([^)]*\)\s*->|[\w_$]+\s*->")
    RE_STREAMS = re.compile(r"\.(?:stream|parallelStream)\(\)")
    RE_ANNOTATION_USAGE = re.compile(r"@[A-Z][a-zA-Z0-9_$]*")
    RE_MODULES = re.compile(r"\b(?:module|requires|exports|provides|uses|opens)\b")
    RE_EXCEPTIONS = re.compile(r"\b(?:try|catch|finally|throw|throws)\b")
    RE_THREADS = re.compile(r"\b(?:Thread|Runnable|ExecutorService|Callable|Future)\b")
    RE_SYNCHRONIZED = re.compile(r"\bsynchronized\b")
    RE_REFLECTION = re.compile(r"\b(?:Class|Method|Field|Constructor|Reflect|MethodHandles)\b")
    RE_TEXT_BLOCKS = re.compile(r'"""[\s\S]*?"""')
    RE_VIRTUAL_THREADS = re.compile(r"\b(?:ofVirtual|startVirtualThread)\b")
    RE_PREVIEW = re.compile(r"\b--enable-preview\b|@PreviewFeature")

    # Version detector pattern e.g. @since 17, --release 21, @requires jdk.version
    RE_JAVA_VERSION = re.compile(r"(?:@since|--release|source|target)\s+([0-9]+)")

    # Symbols
    RE_METHOD = re.compile(r"\b(?:public|protected|private|static|final|native|synchronized|abstract|default)?\s+(?:<[^>]+>\s+)?([a-zA-Z0-9_<>\[\]]+)\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*(?:throws\s+[a-zA-Z0-9_$,\s]+)?\s*[\{;]")
    RE_FIELD = re.compile(r"\b(?:public|protected|private|static|final|transient|volatile)\s+([a-zA-Z0-9_<>\[\]]+)\s+([a-zA-Z0-9_$]+)\s*(?:=.*?)?;", re.MULTILINE)

    def analyze(self, file_path: Path, sha256_hash: str, repo_root: Path) -> JavaFileMetadata:
        """Parses a Java file and generates a JavaFileMetadata dataclass instance."""
        abs_path = str(file_path.resolve())
        rel_path = str(file_path.relative_to(repo_root)) if repo_root in file_path.parents or file_path.is_relative_to(repo_root) else str(file_path)

        meta = JavaFileMetadata(
            filename=file_path.name,
            absolute_path=abs_path,
            relative_path=rel_path,
            sha256=sha256_hash,
            size=file_path.stat().st_size
        )

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return meta

        lines = content.splitlines()
        meta.lines = len(lines)

        # Count comments
        comment_lines = 0
        in_block_comment = False
        for line in lines:
            stripped = line.strip()
            if in_block_comment:
                comment_lines += 1
                if "*/" in stripped:
                    in_block_comment = False
            elif stripped.startswith("/*"):
                comment_lines += 1
                if "*/" not in stripped:
                    in_block_comment = True
            elif stripped.startswith("//"):
                comment_lines += 1

        meta.comment_count = comment_lines

        # Package & Imports
        pkg_match = self.RE_PACKAGE.search(content)
        meta.package = pkg_match.group(1) if pkg_match else ""
        meta.imports = self.RE_IMPORT.findall(content)

        # Symbol extraction
        all_classes = self.RE_CLASS.findall(content)
        meta.interfaces = self.RE_INTERFACE.findall(content)
        meta.enums = self.RE_ENUM.findall(content)
        meta.records = self.RE_RECORD.findall(content)
        meta.annotations = self.RE_ANNOTATION_DEF.findall(content)

        if all_classes:
            meta.classes = [all_classes[0]]
            meta.nested_classes = all_classes[1:]

        # Methods, Constructors, Fields
        methods_found = self.RE_METHOD.findall(content)
        for return_type, method_name, params in methods_found:
            if method_name in all_classes:
                meta.constructors.append(f"{method_name}({params})")
            elif method_name not in ("if", "while", "for", "switch", "catch"):
                meta.methods.append(f"{method_name}({params})")

        fields_found = self.RE_FIELD.findall(content)
        meta.fields = [f"{ftype} {fname}" for ftype, fname in fields_found]

        # Java Version Detection
        ver_match = self.RE_JAVA_VERSION.search(content)
        if ver_match:
            meta.java_version = f"JDK {ver_match.group(1)}"

        # Feature Detection per spec #4
        features: Set[str] = set()

        if all_classes: features.add("classes")
        if meta.interfaces: features.add("interfaces")
        if "abstract" in content: features.add("abstract classes")
        if meta.enums: features.add("enums")
        if meta.records: features.add("records")
        if self.RE_SEALED.search(content): features.add("sealed classes")
        if self.RE_GENERICS.search(content): features.add("generics")
        if self.RE_WILDCARD.search(content): features.add("wildcards")
        if self.RE_ARRAY.search(content): features.add("arrays")
        if self.RE_LOOPS.search(content): features.add("loops")
        if self.RE_SWITCH_EXPR.search(content): features.add("switch expressions")
        if self.RE_PATTERN_MATCHING.search(content): features.add("pattern matching")
        if self.RE_LAMBDAS.search(content): features.add("lambdas")
        if self.RE_STREAMS.search(content): features.add("streams")
        if self.RE_ANNOTATION_USAGE.search(content): features.add("annotations")
        if self.RE_MODULES.search(content): features.add("modules")
        if self.RE_EXCEPTIONS.search(content): features.add("exceptions")
        if self.RE_THREADS.search(content): features.add("threads")
        if self.RE_SYNCHRONIZED.search(content): features.add("synchronized")
        if self.RE_REFLECTION.search(content): features.add("reflection")
        if self.RE_TEXT_BLOCKS.search(content): features.add("text blocks")
        if self.RE_VIRTUAL_THREADS.search(content): features.add("virtual threads")
        if self.RE_PREVIEW.search(content): features.add("preview features")

        meta.features = sorted(list(features))

        # Expected compile check heuristic (jtreg tags @compile/fail)
        if "@compile/fail" in content or "@build/fail" in content:
            meta.expected_compile = "fail"
        elif "@compile" in content or "@run" in content:
            meta.expected_compile = "pass"

        return meta
