import hashlib
import json
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

repo_root = Path(".").resolve()
scratch_dir = repo_root / "data" / "raw"
scratch_dir.mkdir(parents=True, exist_ok=True)
sample_corpus_file = scratch_dir / "tiny_sample_corpus.txt"

# Sample text containing English, numbers, Tamil, and emojis
corpus_text = """
The Large Language Model is built from scratch using pure CPU execution.
Python and PyTorch CPU are used for tensor operations.
Deterministic algorithms guarantee reproducible training across platforms.
வணக்கம் உலகம்! தமிழ் மொழி ஒரு செம்மொழி.
Hello world! 12345 67890.
Special tokens: <PAD>, <UNK>, <BOS>, <EOS>.
Rocket launch 🚀 and robot AI 🤖 on fire 🔥!
"""

sample_corpus_file.write_text(corpus_text, encoding="utf-8")

out1 = Path("checkpoints/test_tok_run1.json")
out2 = Path("checkpoints/test_tok_run2.json")

# Train Run 1
cmd1 = [
    sys.executable,
    "scripts/train_tokenizer.py",
    "--input", str(sample_corpus_file),
    "--output", str(out1),
    "--vocab-size", "300",
    "--min-freq", "1",
]
print("--- Running CLI Training 1 ---")
res1 = subprocess.run(cmd1, capture_output=True, text=True, encoding="utf-8")
print(res1.stdout)
assert res1.returncode == 0, f"Run 1 failed: {res1.stderr}"

# Train Run 2
cmd2 = [
    sys.executable,
    "scripts/train_tokenizer.py",
    "--input", str(sample_corpus_file),
    "--output", str(out2),
    "--vocab-size", "300",
    "--min-freq", "1",
]
print("--- Running CLI Training 2 ---")
res2 = subprocess.run(cmd2, capture_output=True, text=True, encoding="utf-8")
print(res2.stdout)
assert res2.returncode == 0, f"Run 2 failed: {res2.stderr}"

# Compare SHA256 of artifacts for exact determinism
hash1 = hashlib.sha256(out1.read_bytes()).hexdigest()
hash2 = hashlib.sha256(out2.read_bytes()).hexdigest()
print(f"Artifact 1 SHA-256: {hash1}")
print(f"Artifact 2 SHA-256: {hash2}")
assert hash1 == hash2, "Determinism failed! Hashes do not match."
print("Determinism Verified: Both runs produced byte-for-byte identical artifacts!")

# Reload and test encode/decode round-trip
from myllm.tokenizer import Tokenizer
tok = Tokenizer.load(out1)
print(f"Loaded tokenizer with vocab size: {len(tok)}")

test_sentences = [
    "Hello world!",
    "வணக்கம் உலகம்!",
    "Pure CPU LLM: 🚀🤖🔥",
    "123 + 456 = 579.",
]

print("\n--- Round-Trip Verification ---")
for s in test_sentences:
    encoded = tok.encode(s)
    decoded = tok.decode(encoded)
    print(f"Original : {s!r}")
    print(f"Tokens   : {encoded}")
    print(f"Decoded  : {decoded!r}")
    assert s == decoded, f"Mismatch: {s!r} != {decoded!r}"

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

# Cleanup temporary run files
out1.unlink(missing_ok=True)
out2.unlink(missing_ok=True)
sample_corpus_file.unlink(missing_ok=True)
