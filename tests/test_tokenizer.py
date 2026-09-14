"""
Comprehensive test suite for Byte-Level BPE Tokenizer.

Verifies:
- Base vocabulary (all 256 bytes)
- Special tokens (uniqueness, fixed IDs, non-collision)
- Training (growth, merges, deterministic tie-breaking)
- Encoding & Decoding
- Round-trip guarantee: decode(encode(text)) == text
- Save / Load serialization roundtrip
- Deterministic reproducibility
- Edge cases (empty, single char, repeated chars, long text, unseen vocabulary)
- Invalid input handling
- CLI smoke test
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List
import pytest
from myllm.tokenizer import (
    BASE_VOCAB_SIZE,
    BOS_ID,
    BOS_TOKEN,
    EOS_ID,
    EOS_TOKEN,
    PAD_ID,
    PAD_TOKEN,
    UNK_ID,
    UNK_TOKEN,
    BPETrainer,
    Tokenizer,
    Vocabulary,
)
from myllm.tokenizer.bpe import chunk_to_byte_tokens, split_text_into_chunks


# Sample diverse texts for round-trip testing
SAMPLE_TEXTS: List[str] = [
    "Hello world",
    "Hello, world!",
    "123456789",
    "Python is powerful.",
    "Tamil text",
    "தமிழ்",
    "வணக்கம் உலகம்",
    "🚀🤖🔥",
    "Special symbols: !@#$%^&*()_+-=[]{}|;':\",./<>?`~",
    "Multiline\nText\tWith\r\nTabs   and    multiple spaces!",
    "Mixed language: Hello உலகம் 123 🚀!",
    "",  # Empty string
    "a",  # Single character
    "aaaaabbbbbccccc",  # Highly repeated characters
    "The quick brown fox jumps over the lazy dog. " * 20,  # Long text
]


class TestBaseVocabularyAndSpecialTokens:
    def test_base_vocab_size(self) -> None:
        """Verify that base vocabulary contains exactly 260 tokens."""
        vocab = Vocabulary()
        assert len(vocab) == BASE_VOCAB_SIZE
        assert BASE_VOCAB_SIZE == 260

    def test_special_tokens_unique_and_deterministic(self) -> None:
        """Verify that special tokens have fixed, deterministic, and non-colliding IDs."""
        vocab = Vocabulary()
        assert vocab.get_special_token_id(PAD_TOKEN) == PAD_ID == 0
        assert vocab.get_special_token_id(UNK_TOKEN) == UNK_ID == 1
        assert vocab.get_special_token_id(BOS_TOKEN) == BOS_ID == 2
        assert vocab.get_special_token_id(EOS_TOKEN) == EOS_ID == 3

        special_ids = [PAD_ID, UNK_ID, BOS_ID, EOS_ID]
        assert len(set(special_ids)) == 4, "All special token IDs must be unique"

    def test_all_256_bytes_represented(self) -> None:
        """Verify that all 256 byte values (0x00 to 0xFF) are mapped to IDs 4 to 259."""
        vocab = Vocabulary()
        for b in range(256):
            expected_id = b + 4
            assert vocab.contains_id(expected_id)
            assert vocab.id_to_bytes(expected_id) == bytes([b])
            assert vocab.bytes_to_id(bytes([b])) == expected_id

    def test_special_tokens_cannot_be_merged(self) -> None:
        """Verify that attempting to merge a special token raises ValueError."""
        vocab = Vocabulary()
        with pytest.raises(ValueError):
            vocab.add_merge(PAD_ID, 4)
        with pytest.raises(ValueError):
            vocab.add_merge(4, EOS_ID)


class TestBPETraining:
    @pytest.fixture
    def corpus(self) -> List[str]:
        return [
            "low low low low low",
            "lower lower lower",
            "newest newest newest newest",
            "widest widest widest",
            "தமிழ் வணக்கம் தமிழ் உலகம்",
        ]

    def test_training_grows_vocabulary(self, corpus: List[str]) -> None:
        """Verify that training BPE expands vocabulary and generates merge rules."""
        target_vocab = 280  # 260 base + 20 merges
        trainer = BPETrainer(vocab_size=target_vocab, min_pair_frequency=2)
        vocab, merges = trainer.train(corpus)

        assert len(merges) == 20
        assert len(vocab) == target_vocab
        assert len(vocab.merges_list) == 20

    def test_min_frequency_cutoff(self) -> None:
        """Verify trainer stops if no pairs satisfy min_pair_frequency."""
        corpus = ["unique_word_alpha", "unique_word_beta"]
        trainer = BPETrainer(vocab_size=300, min_pair_frequency=5)
        vocab, merges = trainer.train(corpus)
        assert len(vocab) == BASE_VOCAB_SIZE
        assert len(merges) == 0

    def test_deterministic_tie_breaking(self, corpus: List[str]) -> None:
        """Verify that training twice on the exact same corpus yields identical merges and token IDs."""
        trainer1 = BPETrainer(vocab_size=280, min_pair_frequency=2)
        vocab1, merges1 = trainer1.train(corpus)

        trainer2 = BPETrainer(vocab_size=280, min_pair_frequency=2)
        vocab2, merges2 = trainer2.train(corpus)

        assert merges1 == merges2
        assert len(vocab1) == len(vocab2)
        assert vocab1.merges_list == vocab2.merges_list


class TestEncodingAndDecoding:
    @pytest.fixture
    def trained_tokenizer(self) -> Tokenizer:
        corpus = [
            "Hello world! This is a test of Byte-Level BPE tokenizer.",
            "Python is powerful and expressive.",
            "தமிழ் மொழியில் வணக்கம் உலகம்.",
            "123456789 987654321 0000",
            "🚀 🤖 🔥 Symbols and emojis everywhere!",
        ]
        return Tokenizer.train(corpus=corpus, vocab_size=300, min_pair_frequency=2)

    def test_lossless_pretokenization_partition(self) -> None:
        """Verify that pre-tokenization chunking is strictly lossless."""
        for text in SAMPLE_TEXTS:
            chunks = split_text_into_chunks(text)
            assert "".join(chunks) == text, f"Pretokenization was not lossless for: {text!r}"

    @pytest.mark.parametrize("text", SAMPLE_TEXTS)
    def test_round_trip_guarantee(self, trained_tokenizer: Tokenizer, text: str) -> None:
        """Verify decode(encode(text)) == text for all test strings."""
        tokens = trained_tokenizer.encode(text)
        reconstructed = trained_tokenizer.decode(tokens)
        assert reconstructed == text, f"Round-trip failed for {text!r}: got {reconstructed!r}"

    def test_round_trip_untrained_base_tokenizer(self) -> None:
        """Verify round-trip holds even with an untrained base tokenizer (pure bytes)."""
        base_tokenizer = Tokenizer()
        for text in SAMPLE_TEXTS:
            tokens = base_tokenizer.encode(text)
            reconstructed = base_tokenizer.decode(tokens)
            assert reconstructed == text

    def test_encode_with_bos_and_eos(self, trained_tokenizer: Tokenizer) -> None:
        """Verify add_bos and add_eos options."""
        text = "Hello world"
        tokens = trained_tokenizer.encode(text, add_bos=True, add_eos=True)
        assert tokens[0] == BOS_ID
        assert tokens[-1] == EOS_ID

        # When skip_special_tokens=True, decoding strips BOS and EOS
        assert trained_tokenizer.decode(tokens, skip_special_tokens=True) == text

        # When skip_special_tokens=False, special token tags are preserved
        assert trained_tokenizer.decode(tokens, skip_special_tokens=False) == f"{BOS_TOKEN}{text}{EOS_TOKEN}"

    def test_encode_truncation(self, trained_tokenizer: Tokenizer) -> None:
        """Verify max_length truncation works correctly."""
        text = "This is a long sentence meant to test token truncation features."
        tokens = trained_tokenizer.encode(text, max_length=5, truncation=True)
        assert len(tokens) == 5

    def test_decode_invalid_token_id_raises_error(self, trained_tokenizer: Tokenizer) -> None:
        """Verify that invalid token IDs passed to decode raise a clear ValueError."""
        with pytest.raises(ValueError) as exc_info:
            trained_tokenizer.decode([99999])
        assert "Invalid token ID 99999" in str(exc_info.value)

        with pytest.raises(ValueError):
            trained_tokenizer.decode([-1])


class TestSaveAndLoad:
    def test_json_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Verify saving tokenizer to JSON and reloading produces identical encoding and decoding."""
        corpus = [
            "Building LLMs from scratch requires deep understanding.",
            "CPU execution is the target. Determinism is essential.",
            "வணக்கம் தமிழ்நாடு.",
        ]
        tokenizer = Tokenizer.train(corpus=corpus, vocab_size=280, min_pair_frequency=1)

        save_file = tmp_path / "test_tokenizer.json"
        tokenizer.save(save_file)

        assert save_file.exists()

        # Verify JSON is inspectable
        with open(save_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["format_version"] == "1.0"
        assert data["type"] == "byte_level_bpe"
        assert len(data["merges"]) == len(tokenizer.vocab.merges_list)
        assert data["vocab_size"] == len(tokenizer)

        # Reload
        reloaded = Tokenizer.load(save_file)
        assert len(reloaded) == len(tokenizer)

        for text in SAMPLE_TEXTS:
            orig_tokens = tokenizer.encode(text)
            reloaded_tokens = reloaded.encode(text)
            assert orig_tokens == reloaded_tokens
            assert reloaded.decode(reloaded_tokens) == text

    def test_load_malformed_json_raises_error(self, tmp_path: Path) -> None:
        """Verify loading malformed or wrong format JSON raises ValueError."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text(json.dumps({"format_version": "99.0"}), encoding="utf-8")
        with pytest.raises(ValueError):
            Tokenizer.load(bad_file)


class TestEdgeCases:
    def test_empty_string(self) -> None:
        """Verify empty string encodes to empty list and decodes back to empty string."""
        tokenizer = Tokenizer()
        assert tokenizer.encode("") == []
        assert tokenizer.decode([]) == ""

    def test_unseen_unicode_and_emojis(self) -> None:
        """Verify unseen Unicode characters encode and decode losslessly via base byte tokens."""
        tokenizer = Tokenizer.train(corpus=["Only English text in training corpus."], vocab_size=270)
        unseen_text = "இனிய புத்தாண்டு நல்வாழ்த்துகள்! 🛸✨🌌"
        tokens = tokenizer.encode(unseen_text)
        assert tokenizer.decode(tokens) == unseen_text


class TestCLIScript:
    def test_train_tokenizer_cli(self, tmp_path: Path) -> None:
        """Verify scripts/train_tokenizer.py runs successfully via subprocess."""
        input_file = tmp_path / "corpus.txt"
        input_file.write_text(
            "The quick brown fox jumps over the lazy dog.\n"
            "Machine learning on CPU requires modular architecture.\n"
            "வணக்கம் உலகம்.\n",
            encoding="utf-8",
        )
        output_file = tmp_path / "cli_tokenizer.json"

        cmd = [
            sys.executable,
            "scripts/train_tokenizer.py",
            "--input", str(input_file),
            "--output", str(output_file),
            "--vocab-size", "275",
            "--min-freq", "1",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, f"CLI failed with error:\n{result.stderr}\n{result.stdout}"
        assert output_file.exists()
        assert "SUCCESS: Tokenizer trained and saved successfully." in result.stdout

        # Verify the saved tokenizer can be loaded and used
        loaded = Tokenizer.load(output_file)
        assert len(loaded) == 275
        assert loaded.decode(loaded.encode("CPU test")) == "CPU test"
