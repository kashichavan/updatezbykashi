"""
Data models and Metadata JSON generator schema.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class JavaFileMetadata:
    """Dataclass representing full metadata for a single Java source file."""
    filename: str
    absolute_path: str
    relative_path: str
    package: str = ""
    imports: List[str] = field(default_factory=list)
    java_version: str = "unknown"
    categories: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    lines: int = 0
    size: int = 0
    classes: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    enums: List[str] = field(default_factory=list)
    records: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    constructors: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    nested_classes: List[str] = field(default_factory=list)
    comment_count: int = 0
    expected_compile: str = "unknown"
    sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Converts dataclass to a dictionary format conforming to spec requirement #6."""
        d = asdict(self)
        # Ensure category is primary category for spec #6 compatibility
        d["category"] = self.categories[0] if self.categories else "uncategorized"
        return d
