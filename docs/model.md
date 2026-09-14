# GPT-Style Decoder-Only Transformer Architecture

This document details the architecture, mathematical formulations, tensor dimensions, and implementation of the GPT-style decoder-only Transformer built from scratch for **MyLLM**.

---

## 1. Architectural Overview

MyLLM employs a **Pre-LayerNorm GPT-style decoder-only Transformer** architecture built strictly with PyTorch CPU primitives.

```
Input Token IDs: [B, T]
       │
       ▼
Token Embedding: [B, T, C]  +  Learned Positional Embedding: [1, T, C]
       │
       ▼
    Dropout
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ TransformerBlock × n_layer                             │
│   x = x + CausalSelfAttention(LayerNorm(x))            │
│   x = x + MLP(LayerNorm(x))                            │
└────────────────────────────────────────────────────────┘
       │
       ▼
Final LayerNorm: [B, T, C]
       │
       ▼
LM Head (Linear [B, T, vocab_size], tied to Token Embedding)
       │
       ▼
Vocabulary Logits: [B, T, vocab_size]
```

---

## 2. Tensor Dimensions & Hyperparameters

| Symbol | Meaning | Default Value |
| :--- | :--- | :--- |
| $B$ | Batch size | Configurable (e.g. 1 to 16) |
| $T$ | Sequence length / Context size | $128$ (up to `context_length`) |
| $C$ | Embedding dimension (`n_embd`) | $256$ |
| $N$ | Number of transformer layers (`n_layer`) | $4$ |
| $H$ | Number of attention heads (`n_head`) | $4$ |
| $d_h$ | Head dimension (`n_embd // n_head`) | $64$ |
| $V$ | Vocabulary size (`vocab_size`) | $1000$ (or derived from tokenizer) |

---

## 3. Component Details

### A. Token & Positional Embeddings
- **Token Embedding (`wte`)**: Maps discrete token indices $t \in [0, V-1]$ to vectors in $\mathbb{R}^C$.
  $$\text{Input: } [B, T] \implies \text{Output: } [B, T, C]$$
- **Learned Positional Embedding (`wpe`)**: Maps sequence position indices $p \in [0, T-1]$ to vectors in $\mathbb{R}^C$.
  $$\text{Input: } [T] \implies \text{Output: } [T, C] \implies \text{Broadcast to: } [1, T, C]$$
- **Combined Embedding**:
  $$x_0 = \text{Dropout}(wte(\text{input\_ids}) + wpe(\text{positions}))$$
- **Context Bounds Check**: If $T > \text{context\_length}$, `ValueError` is raised immediately.

### B. Multi-Head Causal Self-Attention (`attention.py`)
- **Fused Projection**: Uses a single linear projection $C \to 3C$ to compute Query, Key, and Value vectors simultaneously:
  $$Q, K, V = \text{split}_{C}(\text{Linear}_{C \to 3C}(x))$$
  Reshaped to $[B, H, T, d_h]$.
- **Scaled Dot-Product**:
  $$\text{Scores} = \frac{Q K^T}{\sqrt{d_h}} \in \mathbb{R}^{B \times H \times T \times T}$$
- **Strict Causal Masking**:
  A non-trainable lower-triangular buffer $M \in \{0, 1\}^{T \times T}$ masks out future positions:
  $$\text{Scores}_{i, j} = \begin{cases} \text{Scores}_{i, j} & \text{if } j \le i \\ -\infty & \text{if } j > i \end{cases}$$
  Applying $\text{softmax}$ ensures position $i$ receives exactly zero attention probability from any position $j > i$.
- **Values Aggregation & Projection**:
  $$\text{AttnOutput} = \text{softmax}(\text{Scores}) V \in \mathbb{R}^{B \times H \times T \times d_h}$$
  Recombined heads are projected back through $\text{Linear}_{C \to C}$ with residual dropout.

### C. Feed-Forward Network / MLP (`mlp.py`)
- Standard 4x expansion with GELU activation:
  $$\text{MLP}(x) = \text{Dropout}(\text{Linear}_{4C \to C}(\text{GELU}(\text{Linear}_{C \to 4C}(x))))$$

### D. Transformer Block (`block.py`)
- Pre-LayerNorm residual formulation:
  $$x^{(l)}_{mid} = x^{(l-1)} + \text{Attention}(\text{LayerNorm}_1(x^{(l-1)}))$$
  $$x^{(l)} = x^{(l)}_{mid} + \text{MLP}(\text{LayerNorm}_2(x^{(l)}_{mid}))$$
- Preserves input tensor shape $[B, T, C]$.

### E. LM Head & Weight Tying
- Final projection from hidden representation to vocabulary logits:
  $$\text{Logits} = \text{LMHead}(\text{LayerNorm}_f(x)) \in \mathbb{R}^{B \times T \times V}$$
- **Weight Tying**:
  $$\text{lm\_head.weight} = \text{wte.weight}$$
  Tying input and output weights saves $V \times C$ parameters ($256,000$ parameters for $V=1000, C=256$) and improves representation learning.

---

## 4. Loss Function (Next-Token Prediction)

When `labels` of shape $[B, T]$ are provided to `model(input_ids, labels=labels)`:
- Logits and labels are shifted by 1 position:
  $$\text{shift\_logits} = \text{logits}[:, :-1, :] \quad (\text{predicting tokens } 1 \dots T-1)$$
  $$\text{shift\_labels} = \text{labels}[:, 1:] \quad (\text{target tokens } 1 \dots T-1)$$
- Cross-entropy loss is computed:
  $$\mathcal{L} = -\frac{1}{N} \sum_{i} \log p(\text{target}_i)$$
- Returns `(logits, loss)` where `loss` is a scalar `torch.Tensor`.

---

## 5. Parameter Initialization

Initialization follows standard GPT-2 principles:
- **Linear layers**: $\mathcal{N}(0.0, 0.02)$, biases initialized to $0.0$.
- **Residual projections (`c_proj`)**: Scaled down by the depth of the network:
  $$\sigma = \frac{0.02}{\sqrt{2 \times \text{n\_layer}}}$$
- **Embeddings**: $\mathcal{N}(0.0, 0.02)$.
- **LayerNorm**: Weights initialized to $1.0$, biases to $0.0$.

---

## 6. Model Inspection & Parameter Counting

Utility functions in `myllm.model`:
- `count_parameters(model)`: Returns exact count of total, trainable, and non-trainable parameters, correctly avoiding double-counting tied weights.
- `get_model_summary(model)`: Formats a complete structural breakdown with component parameter counts and estimated memory usage.

### Default Baseline Model Statistics
```
Total Parameters         : 3,259,136 (3.259M)
Trainable Parameters     : 3,259,136
Non-Trainable Parameters : 0
Estimated Parameter Size : 12.43 MB (float32)
```

---

## 7. Python API Example

```python
import torch
from myllm.config import ModelConfig
from myllm.model import GPTModel

# 1. Initialize configuration
config = ModelConfig(
    vocab_size=1000,
    context_length=128,
    n_layer=4,
    n_head=4,
    n_embd=256,
    dropout=0.0,
    bias=True,
    activation="gelu",
    weight_tying=True,
)

# 2. Instantiate model on CPU
model = GPTModel(config)
model.eval()

# 3. Forward pass without labels (inference)
input_ids = torch.tensor([[10, 45, 88, 12]], dtype=torch.long)
logits = model(input_ids)
print("Logits shape:", logits.shape)  # torch.Size([1, 4, 1000])

# 4. Forward pass with labels (training loss)
labels = input_ids.clone()
logits, loss = model(input_ids, labels=labels)
print("Cross-entropy loss:", loss.item())
```
