import { Engine } from './core/Engine';

let activeEngine: Engine | null = null;

window.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('canvas-container');
  if (!container) {
    console.error('Fatal: Failed to locate #canvas-container in the DOM');
    return;
  }

  try {
    activeEngine = new Engine(container);
    await activeEngine.init();
    console.log('🎮 3D Engine Foundation launched successfully!');
  } catch (err) {
    console.error('Fatal initialization error:', err);
  }
});

// Proper cleanup on window unload
window.addEventListener('beforeunload', () => {
  if (activeEngine) {
    activeEngine.dispose();
    activeEngine = null;
  }
});
