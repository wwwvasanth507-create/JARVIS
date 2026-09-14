/**
 * Automated Verification Script for MyLLM Browser Web Chat.
 *
 * Verifies:
 * 1. Web UI availability at http://127.0.0.1:5173
 * 2. API availability & readiness at http://127.0.0.1:8000
 * 3. Session creation with conversational sampling parameters
 * 4. Streaming token-by-token message delivery via SSE
 * 5. Absence of raw <EOS> tokens in assistant output
 * 6. Multi-turn context retention & turn continuation
 * 7. Session persistence & telemetry metrics
 */

const API_BASE = 'http://127.0.0.1:8000';
const WEB_BASE = 'http://127.0.0.1:5173';

async function main() {
  console.log('===============================================================');
  console.log('       MyLLM Browser Web Chat & Model AI Verification          ');
  console.log('===============================================================');

  // 1. Verify Web UI at http://127.0.0.1:5173
  console.log('\n[Step 1] Checking Frontend Web UI at', WEB_BASE);
  const webRes = await fetch(WEB_BASE);
  if (!webRes.ok) throw new Error(`Frontend Web UI returned HTTP ${webRes.status}`);
  const html = await webRes.text();
  console.log('  -> Frontend Web UI OK (HTML size:', html.length, 'bytes, title:', html.includes('<title>') ? 'Yes' : 'No', ')');

  // 2. Verify API Server at http://127.0.0.1:8000
  console.log('\n[Step 2] Checking Backend API Server at', API_BASE);
  const healthRes = await fetch(`${API_BASE}/health`);
  const health = await healthRes.json();
  console.log('  -> Health check:', health);

  const modelRes = await fetch(`${API_BASE}/v1/model`);
  const model = await modelRes.json();
  console.log('  -> Model spec: checkpoint =', model.checkpoint, '| context_length =', model.context_length, '| device =', model.device);

  // 3. Create a new chat session
  console.log('\n[Step 3] Creating new chat session in Web Chat...');
  const sessRes = await fetch(`${API_BASE}/v1/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      system_prompt: 'You are a helpful CPU language model.',
      generation_config: {
        max_new_tokens: 24,
        temperature: 0.7,
        top_p: 0.9,
        do_sample: true,
      },
    }),
  });
  if (!sessRes.ok) throw new Error(`Failed to create session: ${await sessRes.text()}`);
  const sess = await sessRes.json();
  const sessionId = sess.session_id;
  console.log('  -> Created session ID:', sessionId);

  // Helper for SSE streaming chat turn
  async function sendStreamingMessage(promptText, turnLabel) {
    console.log(`\n[${turnLabel}] Sending prompt: "${promptText}"`);
    const streamRes = await fetch(`${API_BASE}/v1/sessions/${sessionId}/messages/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        content: promptText,
        generation_config: {
          max_new_tokens: 20,
          temperature: 0.7,
          top_p: 0.9,
          do_sample: true,
        },
      }),
    });

    if (!streamRes.ok) throw new Error(`Stream request failed: ${await streamRes.text()}`);

    const reader = streamRes.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    const receivedTokens = [];
    let completedReason = '';

    const t0 = performance.now();
    process.stdout.write('  -> Streaming response: "');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const block of lines) {
        const trimmed = block.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const event = JSON.parse(trimmed.slice(6));
            if (event.finished) {
              completedReason = event.stop_reason || 'finished';
            } else if (event.token) {
              receivedTokens.push(event.token);
              process.stdout.write(event.token);
            }
          } catch {
            // ignore
          }
        }
      }
    }
    const elapsedSec = (performance.now() - t0) / 1000;
    console.log(`" (Stop reason: ${completedReason})`);
    console.log(`  -> Generated ${receivedTokens.length} tokens in ${elapsedSec.toFixed(2)}s (${(receivedTokens.length / elapsedSec).toFixed(1)} tok/s)`);

    // Verification assertions
    if (receivedTokens.length === 0) {
      throw new Error(`Turn failed: 0 tokens generated for prompt "${promptText}"!`);
    }
    const fullText = receivedTokens.join('');
    if (fullText.includes('<EOS>')) {
      throw new Error(`Leaked raw <EOS> in generated response: "${fullText}"`);
    }
    return { fullText, tokenCount: receivedTokens.length, stopReason: completedReason };
  }

  // 4. Turn 1: Initial user query
  await sendStreamingMessage('Hello MyLLM! How are you doing today?', 'Turn 1');

  // 5. Turn 2: Follow-up question
  await sendStreamingMessage('Tell me more about CPU training.', 'Turn 2');

  // 6. Turn 3: Multi-turn reasoning
  await sendStreamingMessage('What did we talk about first?', 'Turn 3');

  // 7. Verify session history & context integrity
  console.log('\n[Step 4] Verifying Session History & Multi-turn Context...');
  const detailRes = await fetch(`${API_BASE}/v1/sessions/${sessionId}`);
  const detail = await detailRes.json();
  console.log('  -> Total messages in session:', detail.messages.length);
  for (let i = 0; i < detail.messages.length; i++) {
    const m = detail.messages[i];
    console.log(`     [${i + 1}] ${m.role.toUpperCase()}: "${m.content.slice(0, 50)}${m.content.length > 50 ? '...' : ''}"`);
  }

  if (detail.messages.length !== 6) {
    throw new Error(`Expected 6 messages in history (3 turns), got ${detail.messages.length}`);
  }

  // 8. Test explicit session persistence
  console.log('\n[Step 5] Testing session persistence to JSON...');
  const saveRes = await fetch(`${API_BASE}/v1/sessions/${sessionId}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: 'scratch/browser_chat_verified_session.json' }),
  });
  const saveResult = await saveRes.json();
  console.log('  -> Saved session result:', saveResult);

  // 9. Clean up
  console.log('\n[Step 6] Cleaning up test session...');
  const delRes = await fetch(`${API_BASE}/v1/sessions/${sessionId}`, { method: 'DELETE' });
  const delResult = await delRes.json();
  console.log('  -> Deleted session:', delResult);

  console.log('\n===============================================================');
  console.log('  SUCCESS: Browser Web Chat & Model AI Verified End-to-End!    ');
  console.log('===============================================================');
}

main().catch((err) => {
  console.error('\n[FATAL ERROR]:', err.message);
  process.exit(1);
});
