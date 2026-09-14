# MyLLM: Local Deployment & Production Guide

This guide documents the procedures for installing, configuring, running, and deploying MyLLM as a reproducible, portable, pure CPU application on local hardware or containerized environments.

---

## 1. System Requirements

### Hardware Requirements
- **Processor**: x86_64 / AMD64 modern consumer CPU (Intel Core i3/i5/i7 or AMD Ryzen).
- **Physical Cores**: 2+ cores recommended (4 physical cores optimal).
- **RAM**: 8 GB minimum (16 GB recommended).
- **Storage**: ~2 GB free disk space (repository, dependencies, and model artifacts).
- **GPU**: **None required**. MyLLM is engineered specifically for CPU execution.

### Software Prerequisites
- **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14 (64-bit).
- **Node.js**: v18.0+ (v20+ recommended) and `npm` (for the Web UI frontend).
- **Docker** *(Optional)*: Docker Engine 24+ and Docker Compose v2+ for containerized deployments.

---

## 2. Clean Local Installation Walkthrough

### Step 1: Clone Repository
```powershell
git clone https://github.com/your-username/JARVIS.git
cd JARVIS
```

### Step 2: Create Virtual Environment
```powershell
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install CPU PyTorch
Always install the official CPU build to avoid downloading gigabytes of unnecessary CUDA binaries:
```powershell
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Step 4: Install MyLLM Package
```powershell
# Install runtime package
pip install -e .

# Or install with development & test tools
pip install -e .[dev]
```

### Step 5: Verify Environment & Model Checkpoint
```powershell
# Check CPU threading and verify CPU-only mode
python scripts/check_environment.py

# Verify release model checksums, weights, and CPU inference
python scripts/verify_model.py \
    --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt \
    --tokenizer data/tokenized/tokenizer.json
```

---

## 3. Starting the Services

### Option A: Single-Command Local Launcher
The easiest way to run MyLLM is using the unified launcher:

```powershell
# Start API server and Web UI together
python scripts/run_local.py --with-frontend

# Or start only the API server
python scripts/run_local.py
```

### Option B: Independent Service Startup

#### Terminal 1 — Backend API Server
```powershell
python scripts/serve.py \
    --host 127.0.0.1 \
    --port 8000 \
    --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt \
    --tokenizer data/tokenized/tokenizer.json
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`
- Readiness Probe: `http://127.0.0.1:8000/ready`

#### Terminal 2 — Frontend Web UI
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 4. Production Frontend Build

To build a standalone, optimized static bundle for serving via Nginx, Caddy, or any static file server:

```powershell
cd frontend
# 1. Check TypeScript types
npx tsc --noEmit

# 2. Run Oxlint
npm run lint

# 3. Build production bundle
npm run build
```

The output bundle is generated in `frontend/dist/`:
- `dist/index.html`
- `dist/assets/*.css`
- `dist/assets/*.js`

---

## 5. Docker Container Deployment

MyLLM provides a strictly CPU-only Docker image. Model weights are **not** baked into the image; they are mounted as read-only volumes for maximum flexibility and clean portability.

### Option A: Docker Compose (Recommended)
```bash
# Build image and start API container
docker compose up --build -d

# View real-time logs
docker compose logs -f

# Check container health
docker compose ps
```

### Option B: Docker CLI
```bash
# 1. Build CPU image
docker build -t myllm:cpu-0.1.0 .

# 2. Run container with mounted models and data
docker run -d \
  --name myllm_api \
  -p 8000:8000 \
  -v $(pwd)/experiments/phase7/phase7_sft_run/checkpoints:/app/models:ro \
  -v $(pwd)/data/tokenized:/app/data:ro \
  -v $(pwd)/scratch:/app/scratch:rw \
  myllm:cpu-0.1.0

# 3. Verify health
curl http://127.0.0.1:8000/ready
```

---

## 6. Service Health & Readiness Probes

MyLLM provides two complementary monitoring endpoints:

| Endpoint | Target | Purpose | Computational Cost |
| :--- | :---: | :--- | :---: |
| `GET /health` | Liveness | Verifies that the ASGI process is running and alive. | Near zero ($< 1$ ms) |
| `GET /ready` | Readiness | Verifies that the model checkpoint and tokenizer are actively loaded on CPU and ready for inference. | Fast lookup ($< 2$ ms) |

Example `/ready` response:
```json
{
  "status": "ready",
  "ready": true,
  "model_loaded": true,
  "parameter_count": 136960,
  "context_length": 64,
  "device": "cpu"
}
```

---

## 7. Configuration Precedence

Configuration parameters are resolved using the following order of precedence:
1. **Command-Line Arguments** (`--checkpoint`, `--host`, `--port`, `--device`)
2. **Environment Variables** (`VITE_API_URL`, etc.)
3. **YAML Configuration Files** (`configs/base.yaml` or scaling profiles)
4. **Programmatic Dataclass Defaults** (`ServerConfig`, `ModelConfig`)

---

## 8. Security & Local Architecture

> [!WARNING]
> **Local Deployment Security Model**:
> - MyLLM is strictly designed as a **local desktop/developer application**.
> - The API server has **no authentication, no authorization, and no TLS encryption**.
> - By default, the server binds strictly to loopback (`127.0.0.1`).
> - Binding to `0.0.0.0` exposes the server to all network interfaces. If binding to `0.0.0.0`, ensure the port is protected behind a reverse proxy (such as Nginx or Caddy) with TLS and authentication.
> - Request logging is privacy-conscious: user message content is **not** logged at standard INFO level.
