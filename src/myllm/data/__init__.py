"""
Dataset ingestion, binary token storage, and CPU batching for MyLLM.
"""

from myllm.data.batching import BatchGenerator
from myllm.data.binary import BinaryDatasetWriter, compute_dataset_fingerprint
from myllm.data.corpus import CorpusReader
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.quality import DatasetQualityReport, DatasetQualityValidator
from myllm.data.text import normalize_text
from myllm.data.tokenizer_pipeline import (
    TokenizerPipeline,
    compute_tokenizer_fingerprint,
)

from myllm.data.instruction import (
    IGNORE_INDEX,
    INSTRUCTION_TEMPLATE_VERSION,
    InstructionDataset,
    InstructionExample,
    InstructionTemplate,
    TokenizedInstruction,
    load_instruction_jsonl,
    save_instruction_binary,
    split_instruction_dataset,
    tokenize_instruction_example,
)

__all__ = [
    "CorpusReader",
    "normalize_text",
    "TokenizerPipeline",
    "compute_tokenizer_fingerprint",
    "BinaryDatasetWriter",
    "compute_dataset_fingerprint",
    "DatasetMetadata",
    "TokenDataset",
    "BatchGenerator",
    "DatasetQualityValidator",
    "DatasetQualityReport",
    "InstructionExample",
    "InstructionTemplate",
    "InstructionDataset",
    "TokenizedInstruction",
    "tokenize_instruction_example",
    "load_instruction_jsonl",
    "split_instruction_dataset",
    "save_instruction_binary",
    "INSTRUCTION_TEMPLATE_VERSION",
    "IGNORE_INDEX",
]
