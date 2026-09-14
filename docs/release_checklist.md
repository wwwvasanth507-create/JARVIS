# MyLLM Release Validation Checklist

Use this checklist prior to tagging, releasing, or deploying any version of MyLLM.

---

## 1. Source Hygiene & Versioning
- [ ] Single source of truth for version matches `pyproject.toml` and `myllm.__version__`.
- [ ] Git working directory is clean of temporary logs, `.env` secrets, and IDE artifacts.
- [ ] `.gitignore` properly excludes `.venv*`, `node_modules`, and `dist`.
- [ ] No API keys, tokens, or credentials committed in source code or documentation.
- [ ] `CHANGELOG.md` is updated with complete, factual phase summaries.

---

## 2. Python Package & Dependencies
- [ ] Runtime dependencies in `pyproject.toml` and `requirements.txt` are constrained appropriately.
- [ ] Test and development dependencies are separated into `requirements-dev.txt` / `[project.optional-dependencies]`.
- [ ] Clean installation in a fresh virtual environment (`python -m venv .venv_test && pip install -e .`) succeeds.
- [ ] `python -c "import myllm; print(myllm.version)"` outputs correct version without path hacks.
- [ ] `python -m compileall src/ scripts/ tests/` completes with 0 syntax/compilation errors.

---

## 3. Model Artifact Integrity
- [ ] Model checkpoints exist at designated paths.
- [ ] SHA-256 checksums match `model_manifest.json`:
  - SFT Checkpoint: `6952f99ca36e4c157d46334b1c7134430d2e5659e4d8fd987a56563f971c3bd1`
  - SFT Tokenizer: `2f9822e7c989710a24b3b011c100f9e8ddbaf630e91276533b9af4c709707ce4`
- [ ] Tokenizer cryptographic fingerprint matches checkpoint metadata.
- [ ] `scripts/verify_model.py` passes all 8 verification steps with 100% success.
- [ ] Deterministic greedy test generation on CPU produces identical output tokens.

---

## 4. Backend API & Readiness
- [ ] `python scripts/serve.py` starts cleanly without unhandled exceptions.
- [ ] `GET /health` returns status `ok` on CPU.
- [ ] `GET /ready` returns `ready: true`, confirming model and tokenizer loaded.
- [ ] `GET /v1/model` returns exact parameter count and context length.
- [ ] Synchronous chat message generation completes within performance tolerances.
- [ ] Server-Sent Events (SSE) streaming produces live token stream.
- [ ] Global CPU inference lock prevents thread starvation during concurrent requests.
- [ ] Binding to `0.0.0.0` outputs prominent security warning.

---

## 5. Frontend Web UI
- [ ] `cd frontend && npm install` completes with zero dependency resolution errors.
- [ ] `npx tsc --noEmit` passes with 0 TypeScript errors.
- [ ] `npm run lint` (Oxlint) passes with 0 warnings and 0 errors.
- [ ] `npm run build` produces optimized production bundle in `frontend/dist/`.
- [ ] `npm test` passes all unit and integration test suites.
- [ ] Real browser smoke test confirms browser $\to$ API $\to$ ChatEngine $\to$ model execution path.

---

## 6. Strict CPU Execution Enforcement
- [ ] System environment diagnostic (`scripts/check_environment.py`) confirms:
  - `selected device: cpu`
  - `is_using_cuda: False`
- [ ] CPU intra-op thread count is conservatively configured (optimal: 4 threads).
- [ ] Code never silently selects or attempts to initialize CUDA.

---

## 7. Documentation & Reproducibility
- [ ] `README.md` includes complete setup instructions, architecture diagram, and limitations.
- [ ] Current model quality disclosure is transparent and accurate.
- [ ] `docs/deployment.md` covers local, launcher, and Docker workflows.
- [ ] `release_manifest.json` contains full build and commit metadata.
- [ ] CI workflow (`.github/workflows/ci.yml`) is tested and operational.
