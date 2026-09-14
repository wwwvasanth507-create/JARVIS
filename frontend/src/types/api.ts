/**
 * Strongly-typed API schemas and internal state structures for MyLLM Web UI.
 */

export type Role = 'system' | 'user' | 'assistant';

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: string;
  telemetry?: Telemetry;
  isStreaming?: boolean;
}

export interface Telemetry {
  prompt_tokens: number;
  generated_tokens: number;
  total_tokens: number;
  tokens_per_second: number;
  generation_latency: number;
  stop_reason: string;
  context_truncated: boolean;
  removed_messages: number;
}

export interface HealthResponse {
  status: string;
  service: string;
  device: string;
}

export interface ModelInfo {
  model_name: string;
  checkpoint: string;
  parameter_count: number;
  context_length: number;
  vocab_size: number;
  tokenizer_fingerprint: string;
  device: string;
  kv_cache_supported: boolean;
}

export interface GenerationSettings {
  max_new_tokens: number;
  temperature: number;
  top_k: number;
  top_p: number;
  repetition_penalty: number;
  do_sample: boolean;
  seed: number | null;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  system_prompt?: string | null;
  message_count: number;
}

export interface SessionDetail {
  session_id: string;
  system_prompt: string | null;
  messages: { role: Role; content: string }[];
  generation_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  model_checkpoint: string | null;
}

export interface StreamTokenEvent {
  token: string;
  finished: boolean;
  stop_reason?: string | null;
}

export interface ApiError {
  code: string;
  message: string;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';
