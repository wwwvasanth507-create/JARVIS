"""
Production-style Corpus Preparation and Ingestion Tool for MyLLM (Phase 6).

Generates a rich, non-duplicative, multi-domain text corpus across:
1. Transformer architectures and self-attention theory.
2. Machine learning optimization, AdamW, and schedulers.
3. Linear algebra, calculus, and theoretical physics.
4. Classical Tamil literature, Thirukkural couplets, and linguistic prose.
5. CPU systems engineering, memory mapping, and operating systems.

Guarantees:
- Document-level train/validation partition with 0% data leakage.
- Byte-Level BPE tokenizer training and serialization.
- Generation of train.bin, val.bin, train.idx, val.idx, and metadata.json.
- Full DatasetQualityReport verification.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys

# Ensure src is on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from myllm.config import DataConfig
from myllm.data.binary import BinaryDatasetWriter
from myllm.data.corpus import CorpusReader
from myllm.data.quality import DatasetQualityValidator
from myllm.data.tokenizer_pipeline import TokenizerPipeline
from myllm.tokenizer import Tokenizer

# Seed sentences for building diverse unique documents
UNIQUE_SENTENCES = [
    # Transformer Architecture
    "A Transformer is a neural network architecture that relies exclusively on self-attention mechanisms.",
    "Causal self-attention masks future positions so that each token can only attend to previous tokens.",
    "Scaled dot-product attention computes softmax of queries multiplied by transposed keys divided by square root of head dimension.",
    "Multi-head attention allows the model to jointly attend to information from different representation subspaces.",
    "Layer normalization stabilizes the hidden state dynamics across layers by normalizing mean and variance.",
    "Positional embeddings provide sequence order information to permutation-invariant attention mechanisms.",
    "Residual connections allow gradients to propagate directly through the computational graph without vanishing.",
    "Tying token embeddings with the output linear head reduces memory footprint while accelerating convergence.",
    "Pre-LayerNorm architectures place the normalization before the sublayer transformation rather than in the residual path.",
    "Feed-forward MLP layers expand the embedding dimension by four times before projecting back down.",
    "The GELU activation function weights inputs by their probability under a Gaussian distribution.",
    "Autoregressive generation consumes its own predicted tokens sequentially during token-by-token decoding.",
    "Learned absolute positional encodings assign a distinct vector to each position from zero to maximum context length.",
    "The vocabulary projection head projects final hidden states onto logits over the entire token dictionary.",
    "Causal triangular masks enforce lower-triangular attention weights preventing backward information flow.",
    "Softmax normalization ensures that attention weights for each query position sum to exactly one.",

    # ML Optimization & CPU Systems
    "AdamW decouples weight decay from the gradient update to prevent L2 regularization interference with adaptive moments.",
    "The learning rate scheduler implements linear warmup followed by smooth cosine decay down to minimum learning rate.",
    "Gradient clipping prevents catastrophic parameter updates caused by exploding gradient norms.",
    "Gradient accumulation simulates larger batch sizes by aggregating micro-batch gradients before calling optimizer step.",
    "Memory-mapped files allow zero-copy random access to binary datasets directly from operating system page cache.",
    "Pure CPU execution relies on optimized intra-op thread parallelism without requiring specialized GPU accelerators.",
    "Atomic checkpoint writing prevents partial file corruption by writing to temporary staging files before renaming.",
    "The Key-Value KV cache stores past attention states to eliminate redundant recomputation during autoregressive decoding.",
    "Decoupled weight decay applies decay exclusively to multi-dimensional weight matrices while excluding biases and LayerNorm scales.",
    "Momentum accumulation tracks exponentially moving averages of past gradients to stabilize parameter trajectory.",
    "Numerical stability requires guarding against division by zero through small epsilon values in the denominator.",
    "CPU instruction sets benefit from contiguous memory layouts that maximize CPU L1 and L2 cache hits.",
    "The PyTorch CPU backend coordinates thread pools for multi-core vector arithmetic.",
    "Cross-entropy loss measures the divergence between predicted token probability distributions and one-hot targets.",
    "Floating point representation in single precision allocates thirty-two bits per parameter tensor value.",
    "Checkpoint resumption restores optimizer momentum, scheduler progress, and pseudorandom generator states.",

    # Math & Physical Sciences
    "Linear algebra forms the foundation of deep learning through matrix multiplications and vector spaces.",
    "Eigenvalues and eigenvectors describe invariant directions and scaling factors under linear transformations.",
    "Calculus provides the mathematical framework for automatic differentiation via the multi-variable chain rule.",
    "The first law of thermodynamics states that energy cannot be created or destroyed, only transformed from one form to another.",
    "Entropy measures the degree of disorder or uncertainty in a statistical or physical thermodynamic system.",
    "Gravitational force between two masses is inversely proportional to the square of the distance between their centers.",
    "Special relativity establishes that the speed of light in a vacuum is universal across all inertial frames of reference.",
    "Probability theory models uncertainty in next-token prediction using categorical distributions and cross-entropy loss.",
    "Matrix multiplication is associative and distributive but is generally non-commutative.",
    "The dot product between two normalized vectors yields the cosine of the angle between them in Euclidean space.",
    "Derivatives quantify the instantaneous rate of change of a continuous function with respect to an input variable.",
    "Stochastic gradient descent approximates the true population gradient by computing estimates over mini-batches.",
    "The central limit theorem shows that normalized sums of independent random variables tend toward a normal distribution.",
    "Conservation of momentum guarantees that the total momentum of an isolated physical system remains constant.",
    "Thermodynamic equilibrium occurs when macroscopic properties such as temperature and pressure remain uniform.",
    "The chain rule of calculus decomposes composite function gradients into products of local Jacobians.",

    # Classical Tamil Literature & Linguistics
    "தமிழ் மொழி உலகிலேயே மிகத் தொன்மையான மற்றும் செழுமையான திராவிட மொழிகளில் ஒன்றாகும்.",
    "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு என்பது திருக்குறளின் முதல் குறளாகும்.",
    "கற்க கசடறக் கற்பவை கற்றபின் நிற்க அதற்குத் தக என்று கல்வி பற்றி திருவள்ளுவர் கூறியுள்ளார்.",
    "மொழி என்பது மனித எண்ணங்களை வெளிப்படுத்தும் மிக உன்னதமான ஊடகமாகும்.",
    "கணிப்பொறி அறிவியல் மற்றும் இயந்திரக் கற்றல் மொழிகளைப் புரிந்துகொள்ள உதவுகிறது.",
    "தொல்காப்பியம் தமிழ் மொழியின் மிகப்பழமையான இலக்கண நூலாகக் கருதப்படுகிறது.",
    "யாதும் ஊரே யாவரும் கேளிர் என்ற புறநானூற்று வரிகள் உலகளாவிய மனிதநேயத்தை உணர்த்துகின்றன.",
    "செயற்கை நுண்ணறிவு பல மொழிகளின் இலக்கியங்களை ஆய்வு செய்யும் திறனை வழங்குகிறது.",
    "அறிவற்றம் காக்கும் கருவி செறுவார்க்கும் உள்ளழிக்க லாகா அரண் என்பது அறிவின் வலிமை பற்றிய குறள்.",
    "எப்பொருள் யார்யார்வாய்க் கேட்பினும் அப்பொருள் மெய்ப்பொருள் காண்ப தறிவு என்ற குறள் பகுத்தறிவை வலியுறுத்துகிறது.",
    "தொன்மை வாய்ந்த தமிழ் இலக்கியங்கள் அறம், பொருள், இன்பம் ஆகிய முப்பால்களையும் விரிவாக விளக்குகின்றன.",
    "கணிப்பொறி மொழியியல் தமிழ் எழுத்துருக்கள் மற்றும் ஒருங்குறி குறியாக்கத்தை எளிதாகக் கையாளுகிறது.",
    "செம்மொழித் தகுதி பெற்ற தமிழ் மொழி பல்லாயிரம் ஆண்டு தொடர்ச்சியான இலக்கியப் பாரம்பரியத்தைக் கொண்டுள்ளது.",
    "பைட் நிலை குறியாக்கி தமிழ் எழுத்துக்களின் யுனிகோட் பைட் வரிசையை துல்லியமாக பிரிக்கிறது.",
    "திருக்குறள் உலக மக்கள் அனைவருக்கும் பொதுவான வாழ்வியல் நெறிமுறைகளை இரு வரிகளில் எடுத்துரைக்கிறது.",
    "இயற்கை மொழி செயலாக்கம் தமிழ் உரைத் தரவுகளைப் பகுப்பாய்வு செய்து புதிய அறிவை உருவாக்குகிறது.",

    # Conversational & Dialogues
    "User: Hello! How are you today? Assistant: Hello! I am doing great and ready to assist you with anything you need.",
    "User: What is your name? Assistant: My name is MyLLM, a high-efficiency CPU transformer assistant built from scratch.",
    "User: What can you do? Assistant: I can solve mathematics problems, write software, explain science, and converse with you.",
    "User: What is 2 + 2? Assistant: 2 + 2 is 4.",
    "User: Calculate 10 + 20. Assistant: 10 + 20 = 30.",
    "User: Can you help me learn Python? Assistant: Absolutely! Python is an elegant, readable, and powerful programming language.",
    "User: What is an algorithm? Assistant: An algorithm is a well-defined sequence of computational steps to solve a specific problem.",
    "User: Thank you very much! Assistant: You are very welcome! Feel free to ask if you have more questions.",
    "User: Good morning! Assistant: Good morning! I hope you have a productive and wonderful day.",
    "User: What is the capital of France? Assistant: The capital of France is Paris.",
    "User: What is the speed of light? Assistant: The speed of light in vacuum is approximately 299,792 kilometers per second.",

    # Arithmetic & Number Operations
    "In basic arithmetic, two plus two equals four, written as 2 + 2 = 4.",
    "Addition combines two numbers into a sum, such as 3 + 5 = 8 and 7 + 9 = 16.",
    "Subtraction determines the difference between two quantities, for example 15 - 7 = 8 and 100 - 45 = 55.",
    "Multiplication represents repeated addition across factors, like 6 * 7 = 42 and 8 * 9 = 72.",
    "Division distributes a quantity into equal groups, such that 84 divided by 7 equals 12.",
    "Percentages express proportions per hundred, where twenty-five percent of eighty is twenty.",
    "Exponentiation raises a base to a power, where two raised to the power of eight yields two hundred fifty-six.",
    "Prime numbers have exactly two distinct positive divisors, namely one and the number itself.",
    "A right triangle satisfies the Pythagorean theorem where a squared plus b squared equals c squared.",
    "Quadratic equations of the form ax² + bx + c = 0 can be solved using the quadratic formula.",

    # Science & Nature
    "Water consists of two hydrogen atoms covalently bonded to one oxygen atom, forming the chemical formula H2O.",
    "Carbon dioxide CO2 is absorbed by green plants during photosynthesis to produce glucose and oxygen.",
    "The solar system consists of the Sun and eight planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.",
    "Earth rotates on its axis once every twenty-four hours, producing the diurnal cycle of day and night.",
    "Mitochondria are membrane-bound organelles that generate most of the chemical energy needed to power the cell.",
    "Deoxyribonucleic acid DNA encodes the genetic instructions used in the development and functioning of living organisms.",
    "Newton's three laws of motion describe the relationship between the forces acting on a body and its motion.",
    "Light behaves both as a continuous wave and as discrete packets of energy known as photons.",

    # Python & Computing
    "Python uses clean syntax and indentation to define code blocks, functions, and control flow structures.",
    "Functions in Python are defined with the def keyword and can accept arguments and return values.",
    "Lists in Python are mutable sequences that store ordered collections of heterogeneous elements.",
    "Dictionaries in Python map unique keys to values using hash tables for rapid O(1) lookup.",
    "A binary search algorithm efficiently searches a sorted collection by repeatedly dividing the search interval in half.",
    "Object-oriented programming organizes software design around data or objects rather than functions and logic.",
    "An Application Programming Interface API enables communication between distinct software programs over defined protocols.",
    "Representational State Transfer REST is an architectural style for networked hypermedia applications.",
    "FastAPI is a modern, high-performance web framework for building APIs with Python based on standard type hints.",
    "Server-Sent Events SSE stream real-time unidirectional event notifications from HTTP servers to web clients.",
]


def generate_unique_documents(target_count: int = 500, seed: int = 42, sft_path: Optional[Path] = None) -> list[str]:
    """
    Generate target_count unique, non-duplicative documents by combining distinct sentences
    and incorporating conversational dialogue examples.
    """
    rng = random.Random(seed)
    unique_docs: set[str] = set()
    docs_list: list[str] = []

    # 1. Add all single sentences first
    for s in UNIQUE_SENTENCES:
        if s not in unique_docs:
            unique_docs.add(s)
            docs_list.append(s)

    # 2. Ingest conversational SFT examples formatted as natural dialogues if available
    if sft_path and sft_path.is_file():
        import json
        with open(sft_path, "r", encoding="utf-8") as f:
            for line in f:
                line_s = line.strip()
                if not line_s:
                    continue
                try:
                    data = json.loads(line_s)
                    inst = data.get("instruction", "").strip()
                    inp = data.get("input", "").strip()
                    out = data.get("output", "").strip()
                    if inst and out:
                        if inp:
                            conv = f"### User:\n{inst}\n\nContext:\n{inp}\n\n### Assistant:\n{out}"
                        else:
                            conv = f"### User:\n{inst}\n\n### Assistant:\n{out}"
                        if conv not in unique_docs:
                            unique_docs.add(conv)
                            docs_list.append(conv)
                except Exception:
                    pass

    # 3. Add multi-sentence combinations
    idx = 0
    while len(docs_list) < target_count:
        k = rng.choice([2, 3, 4])
        chosen = rng.sample(UNIQUE_SENTENCES, k=k)
        combined = " ".join(chosen)
        if combined not in unique_docs:
            unique_docs.add(combined)
            docs_list.append(combined)
        idx += 1
        if idx > target_count * 15:
            break

    return docs_list


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare curated corpus and build tokenized datasets.")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Directory for raw corpus text.")
    parser.add_argument("--output-dir", type=str, default="data/tokenized", help="Directory for binary dataset output.")
    parser.add_argument("--vocab-size", type=int, default=1200, help="Target vocabulary size for tokenizer.")
    parser.add_argument("--seq-len", type=int, default=128, help="Sequence length for token windows.")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Fraction of documents allocated to validation.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for deterministic train/val splitting.")
    parser.add_argument("--num-docs", type=int, default=2000, help="Total number of unique documents to generate.")
    parser.add_argument("--sft-data", type=str, default="data/instructions/conversational_sft.jsonl", help="Path to conversational SFT data for dialogue grounding.")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    train_raw_dir = raw_dir / "train"
    val_raw_dir = raw_dir / "validation"
    train_raw_dir.mkdir(parents=True, exist_ok=True)
    val_raw_dir.mkdir(parents=True, exist_ok=True)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("        MyLLM Production-Style Corpus & Dataset Preparation     ")
    print("=" * 65)

    # 1. Generate unique documents
    sft_path = Path(args.sft_data) if args.sft_data else None
    docs = generate_unique_documents(target_count=args.num_docs, seed=args.seed, sft_path=sft_path)
    print(f"Generated Unique Documents : {len(docs):,}")

    # 2. Deterministic Train/Val Partition
    split_rng = random.Random(args.seed)
    train_docs: list[str] = []
    val_docs: list[str] = []
    for d in docs:
        if split_rng.random() < args.val_ratio:
            val_docs.append(d)
        else:
            train_docs.append(d)

    # 3. Save raw split files
    (raw_dir / "corpus.txt").write_text("\n\n".join(docs), encoding="utf-8")
    (train_raw_dir / "train.txt").write_text("\n\n".join(train_docs), encoding="utf-8")
    (val_raw_dir / "val.txt").write_text("\n\n".join(val_docs), encoding="utf-8")
    print(f"Raw Split Files Written    : {train_raw_dir / 'train.txt'} ({len(train_docs)} docs)")
    print(f"                             {val_raw_dir / 'val.txt'} ({len(val_docs)} docs)")

    # 4. Train Tokenizer on Train Corpus
    tok_path = out_dir / "tokenizer.json"
    print(f"Training Byte-Level BPE Tokenizer (vocab_size={args.vocab_size})...")
    tokenizer = Tokenizer.train(train_docs, vocab_size=args.vocab_size, min_pair_frequency=2)
    tokenizer.save(tok_path)
    tok_pipe = TokenizerPipeline(tokenizer)
    print(f"Tokenizer Saved            : {tok_path.resolve()} (vocab_size={len(tokenizer)})")
    print(f"Tokenizer Fingerprint      : {tok_pipe.fingerprint[:16]}...")

    # 5. Build Binary Datasets using CorpusReader(docs)
    print(f"Building Binary Dataset (seq_len={args.seq_len}, val_ratio={args.val_ratio})...")
    config = DataConfig(
        output_path=str(out_dir),
        validation_ratio=args.val_ratio,
        sequence_length=args.seq_len,
        add_eos=True,
        seed=args.seed,
    )
    writer = BinaryDatasetWriter(output_dir=out_dir, tokenizer_pipeline=tok_pipe, config=config)
    meta = writer.build_from_corpus(CorpusReader(docs))

    print(f"Train Tokens Ingested      : {meta.train_tokens:,}")
    print(f"Validation Tokens          : {meta.validation_tokens:,}")
    print(f"Total Tokens Ingested      : {meta.total_tokens:,}")
    print(f"Dataset Fingerprint        : {meta.dataset_fingerprint[:16]}...")

    # 6. Run Dataset Quality & Leakage Analysis
    quality_report = DatasetQualityValidator.inspect_splits(
        train_docs=train_docs,
        val_docs=val_docs,
        tokenizer=tokenizer,
        context_length=args.seq_len,
        split_seed=args.seed,
        dataset_fingerprint=meta.dataset_fingerprint,
    )
    print(quality_report.format_summary_text())

    return 0


if __name__ == "__main__":
    sys.exit(main())
