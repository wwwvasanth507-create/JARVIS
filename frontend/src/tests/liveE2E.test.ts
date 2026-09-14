import { describe, it, expect } from 'vitest';
import { ApiClient } from '../services/apiClient';

describe('Live E2E Integration with Real Phase 9 Server & Phase 7 SFT Model', () => {
  const liveClient = new ApiClient('http://127.0.0.1:8000');

  it('1. GET /health connects to live server and verifies CPU device', async () => {
    const health = await liveClient.checkHealth();
    expect(health.status).toBe('ok');
    expect(health.device).toBe('cpu');
  });

  it('2. GET /v1/model returns real model specifications', async () => {
    const model = await liveClient.getModelInfo();
    expect(model.device).toBe('cpu');
    expect(model.context_length).toBe(64);
    expect(model.parameter_count).toBeGreaterThan(0);
    expect(model.kv_cache_supported).toBe(true);
    expect(model.checkpoint).toContain('experiments/phase7/phase7_sft_run/checkpoints/best.pt');
  });

  it('3. Multi-turn SSE streaming generation with real SFT model', async () => {
    // Create session with system prompt
    const sess = await liveClient.createSession('You are a helpful CPU language model.');
    expect(sess.session_id).toBeDefined();

    // First turn: Stream message 1
    const tokens1: string[] = [];
    let reason1 = '';
    const t0 = performance.now();

    await liveClient.streamMessage(
      sess.session_id,
      'Hello!',
      { max_new_tokens: 16, temperature: 0.7, do_sample: false },
      {
        onToken: (tok) => tokens1.push(tok),
        onComplete: (reason) => {
          reason1 = reason;
        },
      }
    );
    const latency1 = (performance.now() - t0) / 1000;

    expect(tokens1.length).toBeGreaterThan(0);
    expect(reason1).toMatch(/eos|max_new_tokens/);
    console.log(`[Turn 1 Output]: "${tokens1.join('')}" (${tokens1.length} tokens in ${latency1.toFixed(2)}s)`);

    // Verify turn 1 in session state
    const detail1 = await liveClient.getSession(sess.session_id);
    expect(detail1.messages.length).toBe(2);
    expect(detail1.messages[0].role).toBe('user');
    expect(detail1.messages[0].content).toBe('Hello!');
    expect(detail1.messages[1].role).toBe('assistant');

    // Second turn: Stream follow-up message
    const tokens2: string[] = [];
    let reason2 = '';

    await liveClient.streamMessage(
      sess.session_id,
      'What did I just say?',
      { max_new_tokens: 16, do_sample: false },
      {
        onToken: (tok) => tokens2.push(tok),
        onComplete: (reason) => {
          reason2 = reason;
        },
      }
    );

    expect(tokens2.length).toBeGreaterThan(0);
    expect(reason2).toBeDefined();
    console.log(`[Turn 2 Output]: "${tokens2.join('')}"`);

    // Verify turn 2 in session state (multi-turn context retention)
    const detail2 = await liveClient.getSession(sess.session_id);
    expect(detail2.messages.length).toBe(4);

    // Save session to disk
    const saveRes = await liveClient.saveSession(sess.session_id, 'scratch/live_test_session.json');
    expect(saveRes.status).toBe('saved');

    // Clean up: delete session
    const delRes = await liveClient.deleteSession(sess.session_id);
    expect(delRes.status).toBe('deleted');
  });

  it('4. Session isolation between multiple concurrent conversations', async () => {
    const sessA = await liveClient.createSession('Session A Directive');
    const sessB = await liveClient.createSession('Session B Directive');

    expect(sessA.session_id).not.toBe(sessB.session_id);

    // Send to Session A
    await liveClient.sendMessage(sessA.session_id, 'Message for Session A', { max_new_tokens: 8 });

    // Verify Session A has 2 messages, Session B has 0 messages
    const stateA = await liveClient.getSession(sessA.session_id);
    const stateB = await liveClient.getSession(sessB.session_id);

    expect(stateA.messages.length).toBe(2);
    expect(stateB.messages.length).toBe(0);

    // Clean up
    await liveClient.deleteSession(sessA.session_id);
    await liveClient.deleteSession(sessB.session_id);
  });
});
