import React from 'react';
import type { ModelInfo } from '../types/api';

interface ModelModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelInfo: ModelInfo | null;
  loading: boolean;
}

export const ModelModal: React.FC<ModelModalProps> = ({
  isOpen,
  onClose,
  modelInfo,
  loading,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">🧠 Model Architecture & Specifications</h3>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="modal-loading">Loading model metadata...</div>
          ) : modelInfo ? (
            <div className="model-specs-grid">
              <div className="spec-card">
                <span className="spec-label">Model Architecture</span>
                <span className="spec-value">{modelInfo.model_name}</span>
              </div>
              <div className="spec-card">
                <span className="spec-label">Parameter Count</span>
                <span className="spec-value highlight-cyan">
                  {modelInfo.parameter_count.toLocaleString()}
                </span>
              </div>
              <div className="spec-card">
                <span className="spec-label">Context Window</span>
                <span className="spec-value highlight-indigo">
                  {modelInfo.context_length} tokens
                </span>
              </div>
              <div className="spec-card">
                <span className="spec-label">Vocabulary Size</span>
                <span className="spec-value">{modelInfo.vocab_size} tokens</span>
              </div>
              <div className="spec-card">
                <span className="spec-label">Compute Device</span>
                <span className="spec-value highlight-green">
                  {modelInfo.device.toUpperCase()} (Strict CPU)
                </span>
              </div>
              <div className="spec-card">
                <span className="spec-label">KV Attention Cache</span>
                <span className="spec-value">
                  {modelInfo.kv_cache_supported ? '✓ Enabled' : 'Disabled'}
                </span>
              </div>
              <div className="spec-card full-width">
                <span className="spec-label">Checkpoint Identity</span>
                <span className="spec-code">{modelInfo.checkpoint}</span>
              </div>
              <div className="spec-card full-width">
                <span className="spec-label">Tokenizer SHA-256 Fingerprint</span>
                <span className="spec-code">{modelInfo.tokenizer_fingerprint}</span>
              </div>
            </div>
          ) : (
            <div className="modal-error">
              Unable to load model metadata. Ensure the API server is online.
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
