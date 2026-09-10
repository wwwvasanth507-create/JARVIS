# Local Inference Principles

JARVIS adheres strictly to local CPU-first inference principles:
- **No Cloud AI APIs**: 0 requests to OpenAI, Anthropic, Google AI, or external servers.
- **No Ollama Dependency**: Uses direct native C++ / Python bindings (`llama-cpp-python`).
- **CPU Sovereignty**: Operates with `n_gpu_layers = 0` on standard desktop CPUs.
- **Sovereign Privacy**: Conversations, documents, and tool arguments never leave the local computer.
