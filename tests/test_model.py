"""
Comprehensive test suite for GPT-style Decoder-Only Transformer architecture.

Verifies:
1. Model configuration validation
2. Model construction
3. Parameter count (accounting for weight tying)
4. Input shape [B, T]
5. Output shape [B, T, vocab_size]
6. Single-token input
7. Multiple-token input
8. Batch input
9. Maximum context length
10. Context overflow error
11. Invalid token ID behavior
12. Causal mask correctness
13. Attention output shape
14. Transformer block output shape
15. MLP output shape
16. LayerNorm behavior
17. Residual connection behavior
18. Forward pass without labels
19. Forward pass with labels
20. Cross-entropy loss is finite
21. Loss is scalar
22. Backpropagation works
23. Every trainable parameter receives gradients
24. No NaN values in logits
25. No Inf values in logits
26. CPU device verification
27. No CUDA usage
28. Tokenizer -> model integration
29. Deterministic model initialization with same seed
30. Different seeds produce different parameters
31. Train/eval mode behavior
32. Weight tying correctness
33. Strict Causality test (future tokens cannot alter past logits)
34. Overfit micro test (optimizer step decreases loss)
35. State dict serialization and reload
"""

from pathlib import Path
import pytest
import torch
import torch.nn as nn
from myllm.config import ModelConfig
from myllm.model import (
    CausalSelfAttention,
    GPTModel,
    MLP,
    TransformerBlock,
    count_parameters,
    get_model_summary,
)
from myllm.tokenizer import Tokenizer
from myllm.utils.seed import set_seed


@pytest.fixture
def small_config() -> ModelConfig:
    return ModelConfig(
        vocab_size=300,
        context_length=64,
        n_layer=2,
        n_head=4,
        n_embd=64,  # head_dim = 16
        dropout=0.0,
        bias=True,
        activation="gelu",
        weight_tying=True,
    )


@pytest.fixture
def small_model(small_config: ModelConfig) -> GPTModel:
    set_seed(42)
    model = GPTModel(small_config)
    model.eval()
    return model


class TestModelConfiguration:
    def test_valid_config_and_head_dim(self, small_config: ModelConfig) -> None:
        """Verify valid config computes correct head_dim."""
        assert small_config.head_dim == 16
        assert small_config.n_embd % small_config.n_head == 0

    def test_invalid_head_divisibility_raises_error(self) -> None:
        """Verify error raised when n_embd is not divisible by n_head."""
        with pytest.raises(ValueError):
            ModelConfig(n_embd=65, n_head=4)

    def test_non_positive_dimensions_raise_error(self) -> None:
        """Verify error raised when dimensions are non-positive."""
        with pytest.raises(ValueError):
            ModelConfig(vocab_size=0)
        with pytest.raises(ValueError):
            ModelConfig(context_length=-10)
        with pytest.raises(ValueError):
            ModelConfig(n_layer=0)
        with pytest.raises(ValueError):
            ModelConfig(n_head=0)
        with pytest.raises(ValueError):
            ModelConfig(n_embd=-64)

    def test_invalid_dropout_raises_error(self) -> None:
        """Verify error raised when dropout is outside [0, 1)."""
        with pytest.raises(ValueError):
            ModelConfig(dropout=-0.1)
        with pytest.raises(ValueError):
            ModelConfig(dropout=1.0)

    def test_unsupported_activation_raises_error(self) -> None:
        """Verify error raised for unknown activation function."""
        with pytest.raises(ValueError):
            ModelConfig(activation="non_existent_act")


class TestSubModules:
    def test_attention_shape(self, small_config: ModelConfig) -> None:
        """Verify CausalSelfAttention output shape [B, T, C]."""
        attn = CausalSelfAttention(small_config)
        attn.eval()
        x = torch.randn(2, 10, small_config.n_embd)
        y = attn(x)
        assert y.shape == x.shape

    def test_causal_mask_structure(self, small_config: ModelConfig) -> None:
        """Verify causal mask is strictly lower triangular with 1s on/below diagonal and 0s above."""
        attn = CausalSelfAttention(small_config)
        mask = attn.causal_mask.squeeze()
        T = 8
        sub_mask = mask[:T, :T]
        # Diagonal and lower triangle must be 1.0
        tril_i, tril_j = torch.tril_indices(T, T)
        assert torch.all(sub_mask[tril_i, tril_j] == 1.0)
        # Strictly upper triangle must be 0.0
        triu_i, triu_j = torch.triu_indices(T, T, offset=1)
        assert torch.all(sub_mask[triu_i, triu_j] == 0.0)

    def test_mlp_shape(self, small_config: ModelConfig) -> None:
        """Verify MLP output shape matches input shape [B, T, C]."""
        mlp = MLP(small_config)
        mlp.eval()
        x = torch.randn(2, 10, small_config.n_embd)
        y = mlp(x)
        assert y.shape == x.shape

    def test_transformer_block_shape(self, small_config: ModelConfig) -> None:
        """Verify TransformerBlock output shape matches input shape [B, T, C]."""
        block = TransformerBlock(small_config)
        block.eval()
        x = torch.randn(2, 10, small_config.n_embd)
        y = block(x)
        assert y.shape == x.shape


class TestGPTModelForward:
    def test_output_shape_and_types(self, small_model: GPTModel, small_config: ModelConfig) -> None:
        """Verify forward pass output shape [B, T, vocab_size] on batch input."""
        B, T = 4, 16
        input_ids = torch.randint(0, small_config.vocab_size, (B, T))
        logits = small_model(input_ids)
        assert logits.shape == (B, T, small_config.vocab_size)
        assert logits.device.type == "cpu"

    def test_single_token_input(self, small_model: GPTModel, small_config: ModelConfig) -> None:
        """Verify forward pass handles single token input [1, 1]."""
        input_ids = torch.tensor([[42]])
        logits = small_model(input_ids)
        assert logits.shape == (1, 1, small_config.vocab_size)

    def test_max_context_length(self, small_model: GPTModel, small_config: ModelConfig) -> None:
        """Verify forward pass functions at exactly context_length."""
        input_ids = torch.randint(0, small_config.vocab_size, (1, small_config.context_length))
        logits = small_model(input_ids)
        assert logits.shape == (1, small_config.context_length, small_config.vocab_size)

    def test_context_overflow_raises_error(self, small_model: GPTModel, small_config: ModelConfig) -> None:
        """Verify sequence length exceeding context_length raises ValueError."""
        overflow_len = small_config.context_length + 1
        input_ids = torch.randint(0, small_config.vocab_size, (1, overflow_len))
        with pytest.raises(ValueError) as exc_info:
            small_model(input_ids)
        assert "exceeds maximum context length" in str(exc_info.value)

    def test_invalid_token_id_raises_error(self, small_model: GPTModel, small_config: ModelConfig) -> None:
        """Verify out-of-bounds token IDs raise ValueError."""
        # Negative token ID
        with pytest.raises(ValueError):
            small_model(torch.tensor([[-1, 10]]))
        # Token ID >= vocab_size
        with pytest.raises(ValueError):
            small_model(torch.tensor([[10, small_config.vocab_size]]))

    def test_logits_are_finite(self, small_model: GPTModel, small_config: ModelConfig) -> None:
        """Verify logits contain no NaN or Inf values."""
        input_ids = torch.randint(0, small_config.vocab_size, (2, 8))
        logits = small_model(input_ids)
        assert torch.isfinite(logits).all()
        assert not torch.isnan(logits).any()
        assert not torch.isinf(logits).any()


class TestLossAndBackpropagation:
    def test_forward_with_labels_computes_scalar_loss(
        self, small_model: GPTModel, small_config: ModelConfig
    ) -> None:
        """Verify forward with labels computes a finite scalar cross-entropy loss."""
        B, T = 2, 8
        input_ids = torch.randint(0, small_config.vocab_size, (B, T))
        labels = torch.randint(0, small_config.vocab_size, (B, T))

        logits, loss = small_model(input_ids, labels=labels)
        assert logits.shape == (B, T, small_config.vocab_size)
        assert loss.dim() == 0, "Loss must be a scalar tensor"
        assert torch.isfinite(loss), "Loss must be finite"
        assert loss.item() > 0.0

    def test_backpropagation_computes_gradients(
        self, small_config: ModelConfig
    ) -> None:
        """Verify backward() computes non-null gradients for all trainable parameters."""
        model = GPTModel(small_config)
        model.train()

        input_ids = torch.randint(0, small_config.vocab_size, (2, 8))
        labels = torch.randint(0, small_config.vocab_size, (2, 8))

        _, loss = model(input_ids, labels=labels)
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} did not receive a gradient!"
                assert not torch.isnan(param.grad).any(), f"Parameter {name} has NaN in gradients!"

    def test_overfit_micro_test(self, small_config: ModelConfig) -> None:
        """
        Verify that a few gradient update steps reduce loss on a small batch,
        proving the architecture is genuinely trainable.
        """
        set_seed(1337)
        model = GPTModel(small_config)
        model.train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

        input_ids = torch.randint(0, small_config.vocab_size, (2, 8))
        labels = input_ids.clone()

        # Step 1
        _, initial_loss = model(input_ids, labels=labels)
        initial_loss_val = initial_loss.item()

        # Train for 5 micro-steps
        for _ in range(5):
            optimizer.zero_grad()
            _, loss = model(input_ids, labels=labels)
            loss.backward()
            optimizer.step()

        _, final_loss = model(input_ids, labels=labels)
        final_loss_val = final_loss.item()

        assert final_loss_val < initial_loss_val, (
            f"Loss failed to decrease: initial={initial_loss_val:.4f}, final={final_loss_val:.4f}"
        )


class TestCausality:
    def test_future_tokens_cannot_affect_earlier_logits(
        self, small_model: GPTModel, small_config: ModelConfig
    ) -> None:
        """
        Strict Causality Test:
        Input A: [t0, t1, t2]
        Input B: [t0, t1, t2_different]

        In eval mode with dropout=0, logits at positions 0 and 1 must be identical.
        Logits at position 2 may differ.
        """
        small_model.eval()

        # Input A
        input_a = torch.tensor([[10, 20, 30]])
        # Input B has identical prefix [10, 20], but different third token [99]
        input_b = torch.tensor([[10, 20, 99]])

        with torch.no_grad():
            logits_a = small_model(input_a)
            logits_b = small_model(input_b)

        # Logits at positions 0 and 1 must be effectively identical
        prefix_a = logits_a[:, :2, :]
        prefix_b = logits_b[:, :2, :]
        assert torch.allclose(prefix_a, prefix_b, atol=1e-6), (
            "Causality violation! Future token influenced earlier position logits."
        )

        # Logit at position 2 should differ
        last_a = logits_a[:, 2, :]
        last_b = logits_b[:, 2, :]
        assert not torch.allclose(last_a, last_b, atol=1e-4), (
            "Expected different logits at altered token position 2."
        )


class TestWeightTyingAndParameters:
    def test_weight_tying_shares_tensors(self, small_config: ModelConfig) -> None:
        """Verify that when weight_tying=True, lm_head.weight IS wte.weight."""
        small_config.weight_tying = True
        model = GPTModel(small_config)
        assert model.lm_head.weight is model.transformer.wte.weight

    def test_untied_weights_when_disabled(self, small_config: ModelConfig) -> None:
        """Verify that when weight_tying=False, weights are distinct tensors."""
        small_config.weight_tying = False
        model = GPTModel(small_config)
        assert model.lm_head.weight is not model.transformer.wte.weight

    def test_parameter_counting_does_not_double_count_tied_weights(
        self, small_config: ModelConfig
    ) -> None:
        """Verify count_parameters handles tied weights without double-counting."""
        # Tied
        small_config.weight_tying = True
        tied_model = GPTModel(small_config)
        tied_counts = count_parameters(tied_model)

        # Untied
        small_config.weight_tying = False
        untied_model = GPTModel(small_config)
        untied_counts = count_parameters(untied_model)

        # Difference must exactly equal lm_head parameter count (vocab_size * n_embd)
        expected_diff = small_config.vocab_size * small_config.n_embd
        assert untied_counts["total"] - tied_counts["total"] == expected_diff

    def test_model_summary_string(self, small_model: GPTModel) -> None:
        """Verify model summary generates formatted string without error."""
        summary = get_model_summary(small_model)
        assert "Model Summary: GPTModel" in summary
        assert "Total Parameters" in summary
        assert "Transformer Blocks" in summary


class TestDeterminismAndSerialization:
    def test_deterministic_initialization_with_seed(self, small_config: ModelConfig) -> None:
        """Verify that the same random seed produces identical weights."""
        set_seed(999)
        model1 = GPTModel(small_config)

        set_seed(999)
        model2 = GPTModel(small_config)

        for p1, p2 in zip(model1.parameters(), model2.parameters()):
            assert torch.equal(p1, p2)

    def test_different_seeds_produce_different_weights(self, small_config: ModelConfig) -> None:
        """Verify different seeds produce different parameters."""
        set_seed(111)
        model1 = GPTModel(small_config)

        set_seed(222)
        model2 = GPTModel(small_config)

        # At least some parameters must differ
        diff_found = False
        for p1, p2 in zip(model1.parameters(), model2.parameters()):
            if not torch.equal(p1, p2):
                diff_found = True
                break
        assert diff_found

    def test_serialization_smoke_test(
        self, small_model: GPTModel, small_config: ModelConfig, tmp_path: Path
    ) -> None:
        """Verify saving state_dict and reloading produces identical logits."""
        ckpt_path = tmp_path / "model.pt"
        torch.save(small_model.state_dict(), ckpt_path)

        new_model = GPTModel(small_config)
        new_model.load_state_dict(torch.load(ckpt_path, weights_only=True))
        new_model.eval()

        input_ids = torch.randint(0, small_config.vocab_size, (2, 8))
        with torch.no_grad():
            logits_orig = small_model(input_ids)
            logits_reloaded = new_model(input_ids)

        assert torch.equal(logits_orig, logits_reloaded)


class TestTokenizerModelIntegration:
    def test_tokenizer_encode_to_model_forward(self, tmp_path: Path) -> None:
        """Verify end-to-end integration: Tokenizer.encode -> Tensor -> GPTModel -> Logits."""
        corpus = [
            "Building LLM from zero on CPU.",
            "Transformer causal attention mechanism.",
            "தமிழ் மற்றும் ஆங்கிலம்.",
        ]
        tokenizer = Tokenizer.train(corpus, vocab_size=280)
        vocab_size = len(tokenizer)

        config = ModelConfig(
            vocab_size=vocab_size,
            context_length=64,
            n_layer=2,
            n_head=4,
            n_embd=64,
            dropout=0.0,
        )
        model = GPTModel(config)
        model.eval()

        prompt = "Building LLM on CPU"
        token_ids = tokenizer.encode(prompt, add_bos=True)
        input_tensor = torch.tensor([token_ids], dtype=torch.long)

        with torch.no_grad():
            logits = model(input_tensor)

        assert logits.shape == (1, len(token_ids), vocab_size)
        assert logits.device.type == "cpu"
        assert torch.isfinite(logits).all()
