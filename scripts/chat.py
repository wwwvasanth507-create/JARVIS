"""
Interactive Terminal Chat CLI for MyLLM (Phase 8).

Provides an interactive console interface for conversational inference on CPU.
Supports streaming responses, session persistence (/save, /load), history inspection,
and deterministic CPU generation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from myllm.chat import ChatEngine, ChatSession
from myllm.inference.types import GenerationConfig
from myllm.utils.device import resolve_device


def print_banner(engine: ChatEngine, config: GenerationConfig) -> None:
    """Display startup header."""
    print("=" * 60)
    print("  MyLLM Conversational Chat Engine (CPU-First)")
    print("=" * 60)
    print(f"  Model Checkpoint : {engine.checkpoint_path}")
    print(f"  Context Length   : {engine.context_length} tokens")
    print(f"  Tokenizer FP     : {engine.tokenizer_fingerprint[:12]}...")
    print(f"  System Prompt    : {engine.system_prompt or '(None)'}")
    print(f"  Decoding Mode    : {'Greedy' if not config.do_sample else f'Sampled (temp={config.temperature}, top_p={config.top_p})'}")
    print(f"  KV Cache         : {'Enabled' if config.use_cache else 'Disabled'}")
    print("=" * 60)
    print("  Commands:")
    print("    /exit, /quit   : Terminate chat session")
    print("    /reset         : Reset conversation history")
    print("    /history       : Display full conversation history")
    print("    /save <path>   : Save session to JSON file")
    print("    /load <path>   : Load session from JSON file")
    print("    /help          : Show this help message")
    print("=" * 60)
    print()


def handle_command(cmd_line: str, engine: ChatEngine, config: GenerationConfig) -> bool:
    """
    Process slash commands.
    Returns True to continue chat loop, False to exit.
    """
    parts = cmd_line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in {"/exit", "/quit"}:
        print("\nExiting MyLLM Chat. Goodbye!")
        return False

    elif cmd == "/reset":
        engine.reset()
        print("\n[Chat history and KV cache reset successfully.]\n")

    elif cmd == "/help":
        print("\nAvailable Commands:")
        print("  /exit, /quit   - End the chat session")
        print("  /reset         - Clear conversation history and KV cache")
        print("  /history       - Show all messages in this session")
        print("  /save <file>   - Save current session to JSON")
        print("  /load <file>   - Restore session from JSON")
        print("  /help          - Show this help\n")

    elif cmd == "/history":
        history = engine.get_history()
        print("\n--- Conversation History ---")
        if engine.system_prompt:
            print(f"[System]: {engine.system_prompt}")
        if not history:
            print("(History is currently empty)")
        for idx, msg in enumerate(history, 1):
            role_label = msg.role.capitalize()
            print(f"[{idx}] {role_label}: {msg.content}")
        print("----------------------------\n")

    elif cmd == "/save":
        if not arg:
            print("[Error: Must specify a target file path, e.g. /save session.json]\n")
        else:
            try:
                session = engine.create_session()
                save_path = session.save_json(arg)
                print(f"[Session saved to {save_path}]\n")
            except Exception as e:
                print(f"[Error saving session: {e}]\n")

    elif cmd == "/load":
        if not arg:
            print("[Error: Must specify a file path to load, e.g. /load session.json]\n")
        else:
            try:
                session = ChatSession.load_json(arg)
                engine.load_session(session)
                print(f"[Session loaded from {arg} ({len(session.history)} messages restored)]\n")
            except Exception as e:
                print(f"[Error loading session: {e}]\n")

    else:
        print(f"[Unknown command '{cmd}'. Type /help for available commands.]\n")

    return True


def run_chat_loop(engine: ChatEngine, config: GenerationConfig) -> None:
    """Run interactive REPL loop."""
    print_banner(engine, config)

    while True:
        try:
            user_input = input("\nUser > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting MyLLM Chat. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            should_continue = handle_command(user_input, engine, config)
            if not should_continue:
                break
            continue

        # Send user message and stream assistant response
        engine.send_user_message(user_input)
        print("\nAssistant > ", end="", flush=True)

        start_time = time.perf_counter()
        token_count = 0
        stop_reason = "max_new_tokens"

        try:
            for tok in engine.stream_response(config=config):
                if tok.finished:
                    stop_reason = tok.stop_reason or "unknown"
                else:
                    sys.stdout.write(tok.text)
                    sys.stdout.flush()
                    token_count += 1
        except Exception as e:
            print(f"\n[Generation Error: {e}]")
            continue

        elapsed = time.perf_counter() - start_time
        tps = token_count / elapsed if elapsed > 0 else 0.0
        print(f"\n\n  [gen: {token_count} tok | {elapsed:.2f}s ({tps:.1f} tok/s) | stop: {stop_reason}]")


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM Interactive Chat CLI")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="experiments/phase7/phase7_sft_run/checkpoints/best.pt",
        help="Path to trained model checkpoint",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer.json",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=None,
        help="Optional system prompt directive",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=0,
        help="Top-k filtering threshold (0 = disabled)",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.9,
        help="Top-p nucleus filtering (default: 0.9)",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=32,
        help="Maximum tokens to generate per response (default: 32)",
    )
    parser.add_argument(
        "--greedy",
        action="store_true",
        help="Use deterministic greedy decoding instead of sampling",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible generation",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable KV caching (slower naive generation)",
    )

    args = parser.parse_args()

    # Enforce CPU execution
    resolve_device("cpu", strict_cpu=True)

    # Build GenerationConfig
    config = GenerationConfig(
        max_new_tokens=args.max_new_tokens,
        temperature=1.0 if args.greedy else args.temperature,
        top_k=0 if args.greedy else args.top_k,
        top_p=1.0 if args.greedy else args.top_p,
        do_sample=not args.greedy,
        seed=args.seed,
        use_cache=not args.no_cache,
        stop_on_eos=True,
    )

    # Initialize Engine
    try:
        engine = ChatEngine.from_checkpoint(
            checkpoint_path=args.checkpoint,
            tokenizer_path=args.tokenizer,
            system_prompt=args.system,
            default_config=config,
            device="cpu",
        )
    except Exception as e:
        print(f"Error initializing ChatEngine: {e}", file=sys.stderr)
        sys.exit(1)

    run_chat_loop(engine, config)


if __name__ == "__main__":
    main()
