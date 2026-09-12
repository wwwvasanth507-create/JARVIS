import { Time } from '../core/Time';

export class FPSCounter {
  private fpsValueEl: HTMLElement | null = null;
  private msValueEl: HTMLElement | null = null;
  private backendBadgeEl: HTMLElement | null = null;

  constructor() {
    this.fpsValueEl = document.getElementById('fps-val');
    this.msValueEl = document.getElementById('ms-val');
    this.backendBadgeEl = document.getElementById('backend-badge');
  }

  public setBackend(backend: string): void {
    if (this.backendBadgeEl) {
      this.backendBadgeEl.textContent = backend;
      if (backend === 'WebGPU') {
        this.backendBadgeEl.className = 'badge badge-webgpu';
      } else {
        this.backendBadgeEl.className = 'badge badge-webgl';
      }
    }
  }

  public update(): void {
    if (this.fpsValueEl) {
      this.fpsValueEl.textContent = `${Time.fps}`;
      if (Time.fps >= 55) {
        this.fpsValueEl.style.color = '#4ade80'; // Emerald Green
      } else if (Time.fps >= 30) {
        this.fpsValueEl.style.color = '#facc15'; // Yellow
      } else {
        this.fpsValueEl.style.color = '#f87171'; // Red
      }
    }

    if (this.msValueEl) {
      this.msValueEl.textContent = `${Time.frameTimeMs} ms`;
    }
  }
}
