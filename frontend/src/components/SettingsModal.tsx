import React, { useState } from 'react';
import type { GenerationSettings } from '../types/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: GenerationSettings;
  onSaveSettings: (settings: Partial<GenerationSettings>) => void;
  systemPrompt: string;
  onSaveSystemPrompt: (prompt: string) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  systemPrompt,
  onSaveSystemPrompt,
}) => {
  const [localSettings, setLocalSettings] = useState<GenerationSettings>(settings);
  const [localPrompt, setLocalPrompt] = useState<string>(systemPrompt);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveSettings(localSettings);
    onSaveSystemPrompt(localPrompt);
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">⚙️ Generation Settings</h3>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* System Prompt */}
          <div className="form-group">
            <label className="form-label" htmlFor="system-prompt-input">
              System Directive / Prompt
            </label>
            <textarea
              id="system-prompt-input"
              className="form-textarea"
              value={localPrompt}
              onChange={(e) => setLocalPrompt(e.target.value)}
              placeholder="e.g. You are a concise and helpful AI assistant."
              rows={2}
            />
            <span className="form-hint">
              Conditioning directive sent when starting a new chat session.
            </span>
          </div>

          <div className="divider" />

          {/* Decoding Mode */}
          <div className="form-group row-group">
            <div>
              <label className="form-label" htmlFor="sample-toggle">
                Decoding Mode
              </label>
              <span className="form-hint">
                Greedy decoding ensures 100% deterministic outputs.
              </span>
            </div>
            <div className="toggle-group">
              <button
                type="button"
                className={`toggle-btn ${!localSettings.do_sample ? 'toggle-active' : ''}`}
                onClick={() => setLocalSettings((p) => ({ ...p, do_sample: false }))}
              >
                Greedy
              </button>
              <button
                type="button"
                className={`toggle-btn ${localSettings.do_sample ? 'toggle-active' : ''}`}
                onClick={() => setLocalSettings((p) => ({ ...p, do_sample: true }))}
              >
                Sampling
              </button>
            </div>
          </div>

          {/* Max Tokens */}
          <div className="form-group">
            <div className="slider-header">
              <label className="form-label" htmlFor="max-tokens-input">
                Max New Tokens
              </label>
              <span className="slider-val">{localSettings.max_new_tokens}</span>
            </div>
            <input
              id="max-tokens-input"
              type="range"
              min="4"
              max="64"
              value={localSettings.max_new_tokens}
              onChange={(e) =>
                setLocalSettings((p) => ({ ...p, max_new_tokens: Number(e.target.value) }))
              }
              className="form-slider"
            />
          </div>

          {/* Temperature */}
          {localSettings.do_sample && (
            <div className="form-group">
              <div className="slider-header">
                <label className="form-label" htmlFor="temp-input">
                  Temperature
                </label>
                <span className="slider-val">{localSettings.temperature.toFixed(2)}</span>
              </div>
              <input
                id="temp-input"
                type="range"
                min="0.1"
                max="2.0"
                step="0.05"
                value={localSettings.temperature}
                onChange={(e) =>
                  setLocalSettings((p) => ({ ...p, temperature: Number(e.target.value) }))
                }
                className="form-slider"
              />
            </div>
          )}

          {/* Top-P */}
          {localSettings.do_sample && (
            <div className="form-group">
              <div className="slider-header">
                <label className="form-label" htmlFor="top-p-input">
                  Top-P (Nucleus)
                </label>
                <span className="slider-val">{localSettings.top_p.toFixed(2)}</span>
              </div>
              <input
                id="top-p-input"
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={localSettings.top_p}
                onChange={(e) =>
                  setLocalSettings((p) => ({ ...p, top_p: Number(e.target.value) }))
                }
                className="form-slider"
              />
            </div>
          )}

          {/* Seed */}
          <div className="form-group">
            <label className="form-label" htmlFor="seed-input">
              Random Seed (Optional)
            </label>
            <input
              id="seed-input"
              type="number"
              className="form-input"
              value={localSettings.seed ?? ''}
              onChange={(e) =>
                setLocalSettings((p) => ({
                  ...p,
                  seed: e.target.value ? Number(e.target.value) : null,
                }))
              }
              placeholder="Leave empty for unseeded"
            />
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="btn-primary" onClick={handleSave}>
            Apply Settings
          </button>
        </div>
      </div>
    </div>
  );
};
