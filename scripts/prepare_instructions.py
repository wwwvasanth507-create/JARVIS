"""
Synthetic Instruction Dataset Generator for MyLLM (Phase 7).

Generates a diverse, multi-domain synthetic instruction dataset in JSONL format:
- Simple factual extraction & knowledge
- Arithmetic and numeric reasoning
- Summarization & extraction
- Classification (sentiment, domain)
- Formatting & text transformation
- Tamil + English bilingual examples
- Unicode and emoji handling

Clearly annotated as synthetic data for SFT pipeline verification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def generate_synthetic_instructions() -> List[Dict[str, str]]:
    """Generate curated multi-domain synthetic instruction examples."""
    examples: List[Dict[str, str]] = []

    # 1. MyLLM & Machine Learning Factual
    ml_facts = [
        ("What is the primary target hardware of MyLLM?", "", "MyLLM is designed strictly for CPU execution without requiring GPU or CUDA."),
        ("What optimizer is utilized for MyLLM training?", "", "MyLLM utilizes AdamW with decoupled weight decay for optimization."),
        ("Which model architecture is implemented in MyLLM?", "", "MyLLM implements a GPT-style decoder-only Transformer with Pre-LayerNorm."),
        ("What tokenizer algorithm does MyLLM use?", "", "MyLLM uses a custom Byte-Level Byte Pair Encoding (BPE) tokenizer built from scratch."),
        ("Name the three CPU scaling profiles available in MyLLM.", "", "The three profiles are tiny_cpu, small_cpu, and medium_cpu."),
        ("What does causal masking prevent in self-attention?", "", "Causal masking prevents tokens from attending to future positions in the sequence."),
        ("Why does MyLLM tie weights between token embedding and LM head?", "", "Weight tying shares parameters between the input embedding and output projection, reducing parameter count and memory."),
        ("What activation function is used in MyLLM transformer blocks?", "", "MyLLM uses the Gaussian Error Linear Unit (GELU) activation function."),
        ("What does SFT stand for in language model training?", "", "SFT stands for Supervised Fine-Tuning or Supervised Instruction-Tuning."),
        ("What is the purpose of response-only loss masking?", "", "Response-only masking ignores prompt tokens during loss calculation so the model learns only to generate completions."),
    ]
    for inst, inp, out in ml_facts:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 2. Arithmetic & Logic
    arithmetic = [
        ("Calculate 12 + 15.", "", "27"),
        ("What is 8 multiplied by 9?", "", "72"),
        ("Subtract 45 from 100.", "", "55"),
        ("Divide 84 by 7.", "", "12"),
        ("What is 2 raised to the power of 6?", "", "64"),
        ("Compute 35 plus 48.", "", "83"),
        ("Calculate 144 divided by 12.", "", "12"),
        ("What is 15 times 4?", "", "60"),
        ("Evaluate 250 minus 130.", "", "120"),
        ("What is 50 percent of 200?", "", "100"),
    ]
    for inst, inp, out in arithmetic:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 3. Summarization & Key Point Extraction
    summaries = [
        (
            "Summarize the key idea in one short sentence.",
            "Transformers replace recurrent mechanisms entirely with causal self-attention, processing sequences in parallel.",
            "Transformers process sequences in parallel using self-attention rather than recurrence.",
        ),
        (
            "Extract the main benefit described.",
            "KV caching saves previous key and value activations so each subsequent token requires only a single incremental forward step.",
            "KV caching avoids redundant computation by reusing previously computed keys and values.",
        ),
        (
            "Identify the optimization algorithm mentioned.",
            "During Phase 4, the training engine employs the AdamW optimizer with decoupled weight decay.",
            "The algorithm mentioned is AdamW with decoupled weight decay.",
        ),
        (
            "Extract the context window length.",
            "The tiny_cpu configuration profile defines a maximum context length of 64 tokens with 2 layers and 2 attention heads.",
            "The context window length is 64 tokens.",
        ),
        (
            "Summarize the reason for CPU focus.",
            "By targeting standard consumer CPUs, the model ensures complete portability and inspectability on ordinary personal computers.",
            "Standard CPU execution ensures portability and accessibility on ordinary computers.",
        ),
    ]
    for inst, inp, out in summaries:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 4. Classification
    classifications = [
        ("Classify the sentiment as Positive or Negative.", "The model trained quickly and the validation loss dropped steadily.", "Positive"),
        ("Classify the sentiment as Positive or Negative.", "The process crashed with an out-of-memory error and lost unsaved work.", "Negative"),
        ("Classify the sentiment as Positive or Negative.", "All regression tests passed without any errors.", "Positive"),
        ("Classify the hardware category (Compute, Storage, Network).", "Intel Core i7 8-core CPU processor.", "Compute"),
        ("Classify the hardware category (Compute, Storage, Network).", "1 TB NVMe solid state drive.", "Storage"),
        ("Classify the hardware category (Compute, Storage, Network).", "Gigabit Ethernet adapter.", "Network"),
        ("Determine whether this statement is True or False.", "MyLLM requires NVIDIA CUDA hardware to run.", "False"),
        ("Determine whether this statement is True or False.", "AdamW decouples weight decay from the gradient update step.", "True"),
    ]
    for inst, inp, out in classifications:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 5. Formatting & Text Transformation
    formatting = [
        ("Format the names into a comma-separated list.", "Alice\nBob\nCharlie", "Alice, Bob, Charlie"),
        ("Convert the text into uppercase.", "attention is all you need", "ATTENTION IS ALL YOU NEED"),
        ("Convert the text into lowercase.", "DEEP LEARNING WITH PYTORCH", "deep learning with pytorch"),
        ("Format the items as a bulleted list.", "Data, Model, Loss, Optimizer", "- Data\n- Model\n- Loss\n- Optimizer"),
        ("Reverse the words in the sentence.", "apple banana cherry", "cherry banana apple"),
        ("Rephrase to be concise.", "In order to achieve good results, it is necessary that we set the seed.", "Set the seed for reproducible results."),
        ("Extract all numbers from the input.", "The model has 2 layers, 4 heads, and 128 embedding dimensions.", "2, 4, 128"),
    ]
    for inst, inp, out in formatting:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 6. Bilingual & Tamil Linguistics
    bilingual = [
        ("Translate 'வணக்கம்' to English.", "", "Hello"),
        ("Translate 'Hello' to Tamil.", "", "வணக்கம்"),
        ("Translate 'நன்றி' to English.", "", "Thank you"),
        ("Translate 'Thank you' to Tamil.", "", "நன்றி"),
        ("What language is 'தமிழ்'?", "", "'தமிழ்' refers to the Tamil language, a classical Dravidian language."),
        ("Translate 'கணினி' to English.", "", "Computer"),
        ("Translate 'Language Model' to Tamil.", "", "மொழி மாதிரி"),
        ("Write a polite greeting in Tamil.", "", "வணக்கம்! நீங்கள் நலமாக இருக்கிறீர்களா?"),
        ("Name the capital of Tamil Nadu.", "", "The capital of Tamil Nadu is Chennai."),
        ("Translate 'புத்தகம்' to English.", "", "Book"),
    ]
    for inst, inp, out in bilingual:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 7. Code & Programming Logic
    coding = [
        ("Write Python code to add two variables a and b.", "", "result = a + b"),
        ("What does `len(x)` return in Python?", "", "len(x) returns the number of items in a collection or sequence."),
        ("How do you convert string s to an integer in Python?", "", "int(s)"),
        ("Write a Python list containing numbers from 1 to 4.", "", "[1, 2, 3, 4]"),
        ("What PyTorch tensor dtype is used for token IDs?", "", "torch.long (64-bit integer) is used for token IDs."),
    ]
    for inst, inp, out in coding:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # 8. Unicode & Special Characters
    unicode_ex = [
        ("Repeat the following emoji sequence.", "🚀 🤖 ⚡", "🚀 🤖 ⚡"),
        ("Echo the input symbols exactly.", "«MyLLM» — [CPU-First] ✓", "«MyLLM» — [CPU-First] ✓"),
        ("Repeat the Tamil alphabet vowels.", "அ, ஆ, இ, ஈ, உ, ஊ", "அ, ஆ, இ, ஈ, உ, ஊ"),
        ("Echo the math expression.", "E = mc²", "E = mc²"),
        ("Echo the currency symbols.", "$ € £ ¥ ₹", "$ € £ ¥ ₹"),
    ]
    for inst, inp, out in unicode_ex:
        examples.append({"instruction": inst, "input": inp, "output": out})

    # Duplicate some foundational transformations with slight stylistic variance to reach 100+ examples
    more_variations = [
        ("What is 10 + 20?", "", "30"),
        ("What is 7 times 7?", "", "49"),
        ("What is 100 divided by 5?", "", "20"),
        ("What is 60 minus 25?", "", "35"),
        ("Calculate 9 + 16.", "", "25"),
        ("Calculate 11 times 11.", "", "121"),
        ("What is 200 minus 75?", "", "125"),
        ("What is 54 divided by 9?", "", "6"),
        ("What is 13 + 17?", "", "30"),
        ("What is 6 times 8?", "", "48"),
        ("Explain the role of the learning rate scheduler.", "", "The scheduler adjusts the learning rate over time, using warmup and cosine decay to stabilize training."),
        ("What does LayerNorm do in a Transformer?", "", "LayerNorm normalizes features across the hidden dimension to stabilize activations and gradients."),
        ("What is the role of positional embeddings in Transformers?", "", "Positional embeddings provide sequence order information to order-agnostic self-attention."),
        ("Why does causal attention use a triangular mask?", "", "The triangular mask ensures position i cannot attend to positions greater than i."),
        ("What does perplexity measure in language modeling?", "", "Perplexity measures how well a probability model predicts a sample, defined as the exponentiated cross-entropy loss."),
        ("Translate 'நல்வரவு' to English.", "", "Welcome"),
        ("Translate 'Welcome' to Tamil.", "", "நல்வரவு"),
        ("Translate 'பள்ளி' to English.", "", "School"),
        ("Translate 'மகிழ்ச்சி' to English.", "", "Happiness"),
        ("Translate 'Friend' to Tamil.", "", "நண்பன்"),
        ("Classify sentiment.", "The inference latency is exceptionally low and responsive.", "Positive"),
        ("Classify sentiment.", "The generated output contained severe repetitive gibberish.", "Negative"),
        ("Classify sentiment.", "The memory usage remained well within budget constraints.", "Positive"),
        ("Classify sentiment.", "Loss diverged to NaN after ten optimization steps.", "Negative"),
        ("Convert to lowercase.", "TRANSFORMER DECODER ARCHITECTURE", "transformer decoder architecture"),
        ("Convert to uppercase.", "supervised instruction tuning", "SUPERVISED INSTRUCTION TUNING"),
        ("Format as bullet points.", "CPU, Memory, Disk", "- CPU\n- Memory\n- Disk"),
        ("Echo the input text.", "Pure Python and PyTorch CPU implementation.", "Pure Python and PyTorch CPU implementation."),
        ("Identify the programming language.", "def calculate_loss(logits, targets): return loss", "Python"),
        ("Identify the data format.", "{\"instruction\": \"Say hi\", \"output\": \"Hi\"}", "JSON"),
        ("What is the capital of India?", "", "The capital of India is New Delhi."),
        ("Name the largest ocean on Earth.", "", "The Pacific Ocean is the largest ocean on Earth."),
        ("How many days are in a leap year?", "", "A leap year has 366 days."),
        ("What is the chemical symbol for water?", "", "The chemical symbol for water is H2O."),
        ("What gas do plants absorb during photosynthesis?", "", "Plants absorb carbon dioxide (CO2)."),
        ("What does CPU cache do?", "", "CPU cache stores frequently accessed data close to the processor cores for rapid retrieval."),
        ("What is the speed of light in vacuum approximately?", "", "The speed of light in vacuum is approximately 300,000 kilometers per second."),
        ("What is the binary representation of decimal 5?", "", "The binary representation of 5 is 101."),
        ("What is the square root of 81?", "", "9"),
        ("What is 15 percent of 60?", "", "9"),
        ("Calculate 25 + 35.", "", "60"),
        ("What is 10 cubed?", "", "1000"),
        ("Name two input devices for a computer.", "", "Two input devices are keyboard and mouse."),
        ("What does RAM stand for?", "", "RAM stands for Random Access Memory."),
        ("Classify sentiment.", "Training converged rapidly to a low validation perplexity.", "Positive"),
        ("Classify sentiment.", "The model hallucinated fabricated statements repeatedly.", "Negative"),
        ("Translate 'வணக்கம் நண்பா' to English.", "", "Hello friend"),
        ("Translate 'நன்றி பல' to English.", "", "Many thanks"),
        ("Translate 'Good morning' to Tamil.", "", "காலை வணக்கம்"),
        ("Convert to lowercase.", "ARTIFICIAL INTELLIGENCE", "artificial intelligence"),
        ("Convert to uppercase.", "gradient descent algorithm", "GRADIENT DESCENT ALGORITHM"),
        ("Extract digits from the text.", "Token size is 32 and batch is 4.", "32, 4"),
        ("Format as bullet points.", "Alpha, Beta, Gamma", "- Alpha\n- Beta\n- Gamma"),
        ("Echo the text.", "Deterministic random seed ensures reproducible results.", "Deterministic random seed ensures reproducible results."),
        ("What is 40 divided by 8?", "", "5"),
        ("What is 17 minus 9?", "", "8"),
        ("What is 12 times 5?", "", "60"),
        ("What is 99 plus 1?", "", "100"),
        ("Identify the data structure.", "numbers = [10, 20, 30]", "List"),
    ]
    for inst, inp, out in more_variations:
        examples.append({"instruction": inst, "input": inp, "output": out})

    return examples


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic instruction dataset for MyLLM.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/instructions/synthetic_sft.jsonl",
        help="Target output JSONL path.",
    )
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    examples = generate_synthetic_instructions()

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Generated {len(examples)} synthetic instruction examples to: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
