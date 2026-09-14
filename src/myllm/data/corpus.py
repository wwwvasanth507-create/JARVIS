"""
Corpus ingestion and streaming document reader for MyLLM.

Supports single text files, directories of text files (deterministic order),
and iterables of text strings without loading the entire corpus into memory.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator, Iterable, List, Sequence, Tuple, Union

logger = logging.getLogger(__name__)

DEFAULT_EXTENSIONS = (".txt", ".md", ".text")


class CorpusReader:
    """
    Streaming Corpus Ingestion Reader.

    Yields (document_text, document_source_id) tuples one document at a time.
    Guarantees deterministic lexicographic ordering for directories.
    """

    def __init__(
        self,
        source: Union[str, Path, Iterable[str]],
        extensions: Sequence[str] = DEFAULT_EXTENSIONS,
        recursive: bool = True,
    ) -> None:
        self.source = source
        self.extensions = tuple(ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions)
        self.recursive = recursive

    def get_source_files(self) -> List[Path]:
        """
        Discover and return all candidate text files in strict lexicographical order.
        """
        if isinstance(self.source, (str, Path)):
            path = Path(self.source)
            if path.is_file():
                if path.suffix.lower() in self.extensions:
                    return [path]
                else:
                    raise ValueError(
                        f"Source file {path} does not have an allowed extension {self.extensions}."
                    )
            elif path.is_dir():
                glob_pattern = "**/*" if self.recursive else "*"
                matched_files = [
                    p for p in path.glob(glob_pattern)
                    if p.is_file() and p.suffix.lower() in self.extensions
                ]
                # Deterministic sorting across OS platforms using forward-slash POSIX paths
                return sorted(matched_files, key=lambda p: p.as_posix().lower())
            else:
                raise FileNotFoundError(f"Source path not found: {path}")

        return []

    def iter_documents(self) -> Generator[Tuple[str, str], None, None]:
        """
        Stream documents one by one.

        Yields:
            Tuple of (document_text: str, source_identifier: str).
        """
        if isinstance(self.source, (str, Path)):
            files = self.get_source_files()
            if not files:
                logger.warning(f"No text files found in source: {self.source}")
                return

            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                        if content.strip():
                            yield content, file_path.name
                except Exception as exc:
                    logger.error(f"Failed to read document from {file_path}: {exc}")
                    raise
        elif isinstance(self.source, Iterable):
            for idx, item in enumerate(self.source):
                if isinstance(item, str) and item.strip():
                    yield item, f"doc_{idx}"
        else:
            raise TypeError(f"Unsupported corpus source type: {type(self.source)}")
