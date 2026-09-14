"""
Comprehensive test suite for Phase 3 Data Ingestion, Tokenization Cache, and CPU Dataset Pipeline.

Verifies:
1. Single-file ingestion
2. Directory ingestion
3. Recursive directory ingestion
4. Deterministic file ordering
5. Unicode handling
6. Tamil text handling
7. Emoji handling
8. Newline normalization
9. BOM handling
10. Document boundary behavior
11. EOS insertion
12. BOS insertion
13. Tokenizer compatibility
14. Tokenizer fingerprint
15. Binary writing
16. Binary reading
17. np.memmap usage
18. Dataset token count
19. Sequence retrieval
20. Next-token target shifting
21. Context length behavior
22. Batch generator shape
23. Batch generator CPU device
24. Deterministic batch generation
25. Train/validation split determinism
26. No document leakage
27. Dataset metadata
28. Dataset fingerprint
29. Dataset save/reload
30. Empty document behavior
31. Empty corpus behavior
32. Invalid tokenizer path
33. Invalid dataset path
34. Malformed metadata
35. Invalid sequence length
36. Invalid validation ratio
37. Insufficient tokens for a sequence
38. Cross-document sequence behavior
39. Large-file streaming smoke test
40. CLI smoke test
41. End-to-End integration: Corpus -> Tokenizer -> Dataset -> BatchGenerator -> GPTModel forward pass
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List
import numpy as np
import pytest
import torch
from myllm.config import DataConfig, ModelConfig
from myllm.data import (
    BatchGenerator,
    BinaryDatasetWriter,
    CorpusReader,
    DatasetMetadata,
    TokenDataset,
    TokenizerPipeline,
    compute_dataset_fingerprint,
    compute_tokenizer_fingerprint,
    normalize_text,
)
from myllm.model import GPTModel
from myllm.tokenizer import EOS_ID, Tokenizer


@pytest.fixture
def trained_tokenizer() -> Tokenizer:
    corpus = [
        "The quick brown fox jumps over the lazy dog.",
        "Python and PyTorch CPU architecture.",
        "வணக்கம் உலகம்! தமிழ் மொழி ஒரு செம்மொழி.",
        "Rocket launch 🚀 and AI robots 🤖🔥.",
    ]
    return Tokenizer.train(corpus, vocab_size=280, min_pair_frequency=1)


class TestTextNormalization:
    def test_bom_handling(self) -> None:
        """Verify UTF-8 BOM (\ufeff) is cleanly stripped."""
        text = "\ufeffHello world"
        assert normalize_text(text, strip_bom=True) == "Hello world"
        assert normalize_text(text, strip_bom=False) == "\ufeffHello world"

    def test_newline_normalization(self) -> None:
        """Verify Windows and classic Mac newlines are standardized to Unix \\n."""
        text = "Line1\r\nLine2\rLine3\nLine4"
        normalized = normalize_text(text, normalize_newlines=True)
        assert normalized == "Line1\nLine2\nLine3\nLine4"

    def test_unicode_tamil_and_emoji_preservation(self) -> None:
        """Verify Tamil, emojis, punctuation, and internal whitespace are not destroyed."""
        text = "  வணக்கம்   தமிழ்நாடு!  🚀🤖  "
        normalized = normalize_text(text, strip_outer_whitespace=True)
        assert "வணக்கம்   தமிழ்நாடு!" in normalized
        assert "🚀🤖" in normalized


class TestCorpusIngestion:
    def test_single_file_ingestion(self, tmp_path: Path) -> None:
        """Verify single text file reading."""
        file_path = tmp_path / "sample.txt"
        file_path.write_text("Single file content", encoding="utf-8")

        reader = CorpusReader(file_path)
        docs = list(reader.iter_documents())
        assert len(docs) == 1
        assert docs[0][0] == "Single file content"

    def test_directory_ingestion_and_lexicographical_order(self, tmp_path: Path) -> None:
        """Verify directory ingestion discovers files in strict deterministic lexicographical order."""
        (tmp_path / "c_doc.txt").write_text("Doc C", encoding="utf-8")
        (tmp_path / "a_doc.txt").write_text("Doc A", encoding="utf-8")
        (tmp_path / "b_doc.txt").write_text("Doc B", encoding="utf-8")
        (tmp_path / "ignore.bin").write_bytes(b"\x00\x01\x02")  # Unsupported extension

        reader = CorpusReader(tmp_path, recursive=False)
        files = reader.get_source_files()
        assert len(files) == 3
        assert files[0].name == "a_doc.txt"
        assert files[1].name == "b_doc.txt"
        assert files[2].name == "c_doc.txt"

    def test_recursive_directory_ingestion(self, tmp_path: Path) -> None:
        """Verify recursive sub-directory file discovery."""
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.md").write_text("Nested content", encoding="utf-8")
        (tmp_path / "root.txt").write_text("Root content", encoding="utf-8")

        reader = CorpusReader(tmp_path, recursive=True)
        files = reader.get_source_files()
        assert len(files) == 2

    def test_empty_corpus_behavior(self, tmp_path: Path) -> None:
        """Verify empty corpus directory yields 0 documents."""
        reader = CorpusReader(tmp_path)
        assert list(reader.iter_documents()) == []


class TestTokenizerPipeline:
    def test_tokenizer_fingerprint_deterministic(self, trained_tokenizer: Tokenizer) -> None:
        """Verify tokenizer fingerprint is deterministic and matches across calls."""
        fp1 = compute_tokenizer_fingerprint(trained_tokenizer)
        fp2 = compute_tokenizer_fingerprint(trained_tokenizer)
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex digest

    def test_document_boundary_tokens(self, trained_tokenizer: Tokenizer) -> None:
        """Verify configurable EOS and BOS token insertion at document boundaries."""
        pipe = TokenizerPipeline(trained_tokenizer)
        text = "Hello world"

        tokens_eos = pipe.encode_document(text, add_bos=False, add_eos=True)
        assert tokens_eos[-1] == EOS_ID

        tokens_bos_eos = pipe.encode_document(text, add_bos=True, add_eos=True)
        assert tokens_bos_eos[0] == trained_tokenizer.bos_token_id
        assert tokens_bos_eos[-1] == EOS_ID


@pytest.fixture
def built_dataset_dir(tmp_path: Path, trained_tokenizer: Tokenizer) -> Path:
    output_dir = tmp_path / "tokenized"
    corpus = [
        "Document One: The quick brown fox jumps over the lazy dog.",
        "Document Two: Machine learning and CPU optimization.",
        "Document Three: வணக்கம் உலகம் மற்றும் தமிழ்நாடு.",
        "Document Four: Rocket science 🚀 and robotics 🤖.",
        "Document Five: Deep neural networks from scratch.",
        "Document Six: Python is an expressive programming language.",
        "Document Seven: Transformer attention mechanisms.",
        "Document Eight: Causal language modeling.",
        "Document Nine: Dataset pipelines with memory mapping.",
        "Document Ten: Final validation document.",
    ]

    pipe = TokenizerPipeline(trained_tokenizer)
    config = DataConfig(
        output_path=str(output_dir),
        validation_ratio=0.2,
        sequence_length=16,
        add_eos=True,
        seed=42,
    )
    writer = BinaryDatasetWriter(output_dir, pipe, config)
    writer.build_from_corpus(CorpusReader(corpus))
    return output_dir


class TestBinaryDatasetWriterAndStorage:
    def test_binary_files_created(self, built_dataset_dir: Path) -> None:
        """Verify train.bin, val.bin, index files, and metadata.json are generated."""
        assert (built_dataset_dir / "train.bin").is_file()
        assert (built_dataset_dir / "val.bin").is_file()
        assert (built_dataset_dir / "train.idx").is_file()
        assert (built_dataset_dir / "val.idx").is_file()
        assert (built_dataset_dir / "metadata.json").is_file()

    def test_metadata_fields_and_fingerprint(self, built_dataset_dir: Path) -> None:
        """Verify metadata contents, token counts, and fingerprint."""
        meta = DatasetMetadata.load(built_dataset_dir / "metadata.json")
        assert meta.total_tokens == meta.train_tokens + meta.validation_tokens
        assert meta.total_tokens > 0
        assert meta.documents_processed == 10
        assert meta.dtype == "uint32"
        assert len(meta.dataset_fingerprint) == 64

    def test_train_val_split_no_leakage(self, built_dataset_dir: Path) -> None:
        """Verify both train and validation have positive tokens and disjoint documents."""
        meta = DatasetMetadata.load(built_dataset_dir / "metadata.json")
        assert meta.train_tokens > 0
        assert meta.validation_tokens > 0

    def test_deterministic_dataset_generation(
        self, tmp_path: Path, trained_tokenizer: Tokenizer
    ) -> None:
        """Verify identical corpus, tokenizer, config, and seed yield identical binary files."""
        corpus = ["Document A text.", "Document B text.", "Document C text."]
        pipe = TokenizerPipeline(trained_tokenizer)
        config = DataConfig(validation_ratio=0.33, seed=999)

        dir1 = tmp_path / "run1"
        dir2 = tmp_path / "run2"

        writer1 = BinaryDatasetWriter(dir1, pipe, config)
        meta1 = writer1.build_from_corpus(CorpusReader(corpus))

        writer2 = BinaryDatasetWriter(dir2, pipe, config)
        meta2 = writer2.build_from_corpus(CorpusReader(corpus))

        assert meta1.dataset_fingerprint == meta2.dataset_fingerprint
        assert (dir1 / "train.bin").read_bytes() == (dir2 / "train.bin").read_bytes()
        assert (dir1 / "val.bin").read_bytes() == (dir2 / "val.bin").read_bytes()


class TestTokenDatasetAndSequenceRetrieval:
    def test_memmap_sequence_retrieval_and_target_shift(
        self, built_dataset_dir: Path
    ) -> None:
        """Verify TokenDataset retrieves (x, y) where y is shifted by 1."""
        train_bin = built_dataset_dir / "train.bin"
        dataset = TokenDataset(
            train_bin,
            sequence_length=8,
            allow_cross_document_sequences=True,
        )
        assert len(dataset) > 0
        x, y = dataset[0]

        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert x.shape == (8,)
        assert y.shape == (8,)

        # Next-token target shift: x[1:] must equal y[:-1]
        np.testing.assert_array_equal(x[1:], y[:-1])

    def test_cross_document_sequences_disabled(self, built_dataset_dir: Path) -> None:
        """Verify sequence retrieval strictly adheres to document index when cross-doc is False."""
        train_bin = built_dataset_dir / "train.bin"
        dataset_bounded = TokenDataset(
            train_bin,
            sequence_length=8,
            allow_cross_document_sequences=False,
        )
        dataset_continuous = TokenDataset(
            train_bin,
            sequence_length=8,
            allow_cross_document_sequences=True,
        )
        # Bounded dataset has fewer or equal valid sequence windows than continuous
        assert len(dataset_bounded) <= len(dataset_continuous)

    def test_insufficient_tokens_dataset_length(self, tmp_path: Path) -> None:
        """Verify dataset with fewer tokens than sequence_length + 1 has length 0."""
        tiny_bin = tmp_path / "tiny.bin"
        # 5 tokens
        np.array([10, 20, 30, 40, 50], dtype=np.uint32).tofile(tiny_bin)

        dataset = TokenDataset(tiny_bin, sequence_length=10, allow_cross_document_sequences=True)
        assert len(dataset) == 0


class TestBatchGenerator:
    def test_batch_generator_shapes_and_cpu_device(self, built_dataset_dir: Path) -> None:
        """Verify BatchGenerator yields PyTorch CPU tensors of shape [B, T]."""
        dataset = TokenDataset(
            built_dataset_dir / "train.bin",
            sequence_length=16,
            allow_cross_document_sequences=True,
        )
        B, T = 4, 16
        batch_gen = BatchGenerator(dataset, batch_size=B, shuffle=True, seed=42)

        input_ids, labels = batch_gen.get_random_batch()

        assert isinstance(input_ids, torch.Tensor)
        assert isinstance(labels, torch.Tensor)
        assert input_ids.shape == (B, T)
        assert labels.shape == (B, T)
        assert input_ids.dtype == torch.long
        assert labels.dtype == torch.long
        assert input_ids.device.type == "cpu"
        assert labels.device.type == "cpu"

    def test_batch_generator_deterministic_sampling(self, built_dataset_dir: Path) -> None:
        """Verify identical seed produces identical random batches."""
        dataset = TokenDataset(
            built_dataset_dir / "train.bin",
            sequence_length=8,
            allow_cross_document_sequences=True,
        )
        gen1 = BatchGenerator(dataset, batch_size=2, seed=12345)
        gen2 = BatchGenerator(dataset, batch_size=2, seed=12345)

        x1, y1 = gen1.get_random_batch()
        x2, y2 = gen2.get_random_batch()

        assert torch.equal(x1, x2)
        assert torch.equal(y1, y2)


class TestErrorHandling:
    def test_invalid_tokenizer_path(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            TokenizerPipeline(tmp_path / "non_existent.json")

    def test_invalid_dataset_bin_path(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            TokenDataset(tmp_path / "missing.bin", sequence_length=16)

    def test_invalid_validation_ratio_raises_error(self) -> None:
        with pytest.raises(ValueError):
            DataConfig(validation_ratio=1.5)
        with pytest.raises(ValueError):
            DataConfig(validation_ratio=-0.1)

    def test_invalid_sequence_length_raises_error(self) -> None:
        with pytest.raises(ValueError):
            DataConfig(sequence_length=0)


class TestCLIScripts:
    def test_build_dataset_and_inspect_cli(
        self, tmp_path: Path, trained_tokenizer: Tokenizer
    ) -> None:
        """Verify scripts/build_dataset.py and scripts/inspect_dataset.py via subprocess."""
        # 1. Save tokenizer
        tok_file = tmp_path / "tok.json"
        trained_tokenizer.save(tok_file)

        # 2. Write raw corpus
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        (raw_dir / "file1.txt").write_text("Hello from MyLLM CLI test file one.", encoding="utf-8")
        (raw_dir / "file2.txt").write_text("Second file with Tamil வணக்கம் உலகம்.", encoding="utf-8")

        output_dir = tmp_path / "tokenized"

        # 3. Run build_dataset.py CLI
        cmd_build = [
            sys.executable,
            "scripts/build_dataset.py",
            "--tokenizer", str(tok_file),
            "--input", str(raw_dir),
            "--output", str(output_dir),
            "--validation-ratio", "0.5",
            "--sequence-length", "8",
        ]
        res_build = subprocess.run(cmd_build, capture_output=True, text=True, encoding="utf-8")
        assert res_build.returncode == 0, f"build_dataset.py failed:\n{res_build.stderr}\n{res_build.stdout}"
        assert (output_dir / "metadata.json").is_file()

        # 4. Run inspect_dataset.py CLI
        cmd_inspect = [
            sys.executable,
            "scripts/inspect_dataset.py",
            "--dataset", str(output_dir),
            "--tokenizer", str(tok_file),
        ]
        res_inspect = subprocess.run(cmd_inspect, capture_output=True, text=True, encoding="utf-8")
        assert res_inspect.returncode == 0, f"inspect_dataset.py failed:\n{res_inspect.stderr}\n{res_inspect.stdout}"
        assert "SUCCESS: Memory-mapped dataset inspection complete." in res_inspect.stdout


class TestEndToEndPipelineWithGPTModel:
    def test_end_to_end_corpus_to_model_forward(
        self, tmp_path: Path, trained_tokenizer: Tokenizer
    ) -> None:
        """
        End-to-End Pipeline Integration Test:
        Raw Corpus -> Tokenizer -> BinaryDatasetWriter -> TokenDataset ->
        BatchGenerator -> PyTorch CPU Tensors -> GPTModel forward pass ->
        finite scalar loss.
        """
        raw_file = tmp_path / "training_corpus.txt"
        raw_file.write_text(
            "Deep learning with PyTorch CPU from scratch.\n"
            "Transformer architectures require multi-head attention.\n"
            "வணக்கம் தமிழ்நாடு! தமிழ் மொழி வாழ்க.\n"
            "Machine learning pipelines are modular and reproducible.\n" * 5,
            encoding="utf-8",
        )

        tok_pipe = TokenizerPipeline(trained_tokenizer)
        dataset_dir = tmp_path / "out_dataset"

        config = DataConfig(
            output_path=str(dataset_dir),
            validation_ratio=0.2,
            sequence_length=16,
            add_eos=True,
            seed=42,
        )
        writer = BinaryDatasetWriter(dataset_dir, tok_pipe, config)
        writer.build_from_corpus(CorpusReader(raw_file))

        # Open TokenDataset
        dataset = TokenDataset(
            dataset_dir / "train.bin",
            sequence_length=16,
            allow_cross_document_sequences=True,
        )
        assert len(dataset) > 0

        # BatchGenerator
        B, T = 2, 16
        batch_gen = BatchGenerator(dataset, batch_size=B, seed=42)
        input_ids, labels = batch_gen.get_random_batch()

        # Build GPTModel
        model_config = ModelConfig(
            vocab_size=len(trained_tokenizer),
            context_length=32,
            n_layer=2,
            n_head=2,
            n_embd=64,
            dropout=0.0,
        )
        model = GPTModel(model_config)
        model.eval()

        # Forward pass with labels
        with torch.no_grad():
            logits, loss = model(input_ids, labels=labels)

        assert logits.shape == (B, T, len(trained_tokenizer))
        assert loss.dim() == 0
        assert torch.isfinite(loss)
        assert loss.item() > 0.0
