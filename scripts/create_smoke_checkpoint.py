"""
Generate a persistent Phase 4 CPU checkpoint and dataset for Phase 5 verification and demos.
"""

from __future__ import annotations

from pathlib import Path
import sys
from myllm.config import AppConfig, DataConfig, ModelConfig, TrainingConfig
from myllm.data import BinaryDatasetWriter, CorpusReader, TokenDataset, TokenizerPipeline
from myllm.model import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.training import Trainer
from myllm.utils.device import configure_cpu_threads, resolve_device
from myllm.utils.seed import set_seed


def main() -> None:
    set_seed(42)
    device = resolve_device("cpu", strict_cpu=True)
    _ = configure_cpu_threads(4)

    ckpt_dir = Path("checkpoints/smoke")
    data_dir = Path("data/smoke")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    corpus = [
        "MyLLM is a pure CPU decoder-only Transformer language model built from scratch.",
        "Optimization utilizes AdamW with decoupled weight decay for 2D weight matrices.",
        "LayerNorm and bias parameters receive zero weight decay to preserve representation.",
        "தமிழ் மொழி மற்றும் திருக்குறள் ஆதரவு முழுமையாக உள்ளது.",
        "Learning rate scheduling begins with linear warmup followed by smooth cosine decay.",
        "Cross-document sequence boundaries prevent contamination across documents.",
        "Atomic checkpoint writing protects training progress against unexpected interruption.",
        "Robotics 🤖 and machine intelligence 🧠 require deterministic CPU pipelines 🚀.",
    ] * 20

    # 1. Tokenizer
    tok_path = ckpt_dir / "tokenizer.json"
    tokenizer = Tokenizer.train(corpus, vocab_size=320, min_pair_frequency=2)
    tokenizer.save(tok_path)
    tok_pipe = TokenizerPipeline(tokenizer)

    # 2. Binary Dataset
    writer = BinaryDatasetWriter(
        output_dir=data_dir,
        tokenizer_pipeline=tok_pipe,
        config=DataConfig(validation_ratio=0.15, sequence_length=16),
    )
    meta = writer.build_from_corpus(CorpusReader(corpus))

    # 3. Model & AppConfig
    model_cfg = ModelConfig(
        vocab_size=len(tokenizer),
        context_length=32,
        n_layer=2,
        n_head=2,
        n_embd=64,
        dropout=0.0,
        weight_tying=True,
    )
    app_cfg = AppConfig(
        model=model_cfg,
        training=TrainingConfig(
            max_steps=30,
            batch_size=4,
            learning_rate=3e-3,
            min_learning_rate=3e-4,
            warmup_steps=5,
            eval_every_steps=10,
            checkpoint_every_steps=10,
            eval_batches=5,
            save_best=True,
        ),
    )
    app_cfg.paths.checkpoint_dir = str(ckpt_dir)

    model = GPTModel(model_cfg)
    train_ds = TokenDataset(data_dir / "train.bin", sequence_length=16, allow_cross_document_sequences=True)
    val_ds = TokenDataset(data_dir / "val.bin", sequence_length=16, allow_cross_document_sequences=True)

    trainer = Trainer(
        model=model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        config=app_cfg,
        tokenizer_fingerprint=meta.tokenizer_fingerprint,
        dataset_fingerprint=meta.dataset_fingerprint,
    )

    state = trainer.train()
    train_ds.close()
    val_ds.close()

    print(f"Checkpoint saved at: {ckpt_dir / 'best.pt'} (step={state.global_step}, loss={state.train_loss:.4f})")
    print(f"Tokenizer saved at:  {tok_path}")
    print(f"Validation dataset:  {data_dir / 'val.bin'}")


if __name__ == "__main__":
    main()
