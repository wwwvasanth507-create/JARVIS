import { Diagnostics, EngineDiagnostics } from '../engine/Diagnostics';
import { RenderingEngine } from '../engine/RenderingEngine';
import { CharacterController } from '../player/CharacterController';
import { settings, QualityPreset } from '../core/SettingsManager';
import { elevationSampler } from '../world/ElevationSampler';
import type { TestScene } from '../scene/TestScene';

export class DebugOverlay {
  public isOpen: boolean = true;
  private container: HTMLElement | null = null;
  private toggleBtn: HTMLElement | null = null;

  // DOM stat elements
  private statBackend: HTMLElement | null = null;
  private statFps: HTMLElement | null = null;
  private statFrameTime: HTMLElement | null = null;
  private statCalls: HTMLElement | null = null;
  private statTriangles: HTMLElement | null = null;
  private statMemory: HTMLElement | null = null;
  private statPlayerPos: HTMLElement | null = null;
  private statPlayerSpeed: HTMLElement | null = null;
  private statPlayerGround: HTMLElement | null = null;
  private statCameraPos: HTMLElement | null = null;

  // Streaming & Geography stat elements
  private statStreamRegion: HTMLElement | null = null;
  private statStreamChunk: HTMLElement | null = null;
  private statStreamActive: HTMLElement | null = null;
  private statStreamQueue: HTMLElement | null = null;
  private statStreamLoaded: HTMLElement | null = null;

  // Setting inputs
  private shadowCheckbox: HTMLInputElement | null = null;
  private wireframeCheckbox: HTMLInputElement | null = null;
  private presetButtons: NodeListOf<HTMLButtonElement> | null = null;

  constructor() {
    this.cacheDOMElements();
    this.bindEvents();
    this.syncSettingsUI();
  }

  private cacheDOMElements(): void {
    this.container = document.getElementById('debug-overlay');
    this.toggleBtn = document.getElementById('toggle-debug-btn');

    this.statBackend = document.getElementById('stat-backend');
    this.statFps = document.getElementById('stat-fps');
    this.statFrameTime = document.getElementById('stat-frame-time');
    this.statCalls = document.getElementById('stat-calls');
    this.statTriangles = document.getElementById('stat-triangles');
    this.statMemory = document.getElementById('stat-memory');
    this.statPlayerPos = document.getElementById('stat-player-pos');
    this.statPlayerSpeed = document.getElementById('stat-player-speed');
    this.statPlayerGround = document.getElementById('stat-player-ground');
    this.statCameraPos = document.getElementById('stat-camera-pos');

    this.statStreamRegion = document.getElementById('stat-stream-region');
    this.statStreamChunk = document.getElementById('stat-stream-chunk');
    this.statStreamActive = document.getElementById('stat-stream-active');
    this.statStreamQueue = document.getElementById('stat-stream-queue');
    this.statStreamLoaded = document.getElementById('stat-stream-loaded');

    this.shadowCheckbox = document.getElementById('setting-shadows') as HTMLInputElement;
    this.wireframeCheckbox = document.getElementById('setting-wireframe') as HTMLInputElement;
    this.presetButtons = document.querySelectorAll('.preset-btn') as NodeListOf<HTMLButtonElement>;
  }

  private bindEvents(): void {
    this.toggleBtn?.addEventListener('click', () => this.toggle());

    window.addEventListener('keydown', (e) => {
      if (e.code === 'F1' || e.code === 'Backquote') {
        e.preventDefault();
        this.toggle();
      }
    });

    this.shadowCheckbox?.addEventListener('change', (e) => {
      settings.setShadows((e.target as HTMLInputElement).checked);
    });

    this.wireframeCheckbox?.addEventListener('change', (e) => {
      settings.setWireframe((e.target as HTMLInputElement).checked);
    });

    this.presetButtons?.forEach((btn) => {
      btn.addEventListener('click', () => {
        const preset = btn.dataset.preset as QualityPreset;
        if (preset) {
          settings.setPreset(preset);
          this.syncSettingsUI();
        }
      });
    });
  }

  public toggle(): void {
    this.isOpen = !this.isOpen;
    if (this.container) {
      this.container.style.display = this.isOpen ? 'block' : 'none';
    }
  }

  public syncSettingsUI(): void {
    if (this.shadowCheckbox) {
      this.shadowCheckbox.checked = settings.settings.shadows;
    }
    if (this.wireframeCheckbox) {
      this.wireframeCheckbox.checked = settings.settings.wireframe;
    }
    if (this.presetButtons) {
      this.presetButtons.forEach((btn) => {
        if (btn.dataset.preset === settings.settings.preset) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }
  }

  public update(engine: RenderingEngine, player: CharacterController, scene?: TestScene): void {
    if (!this.isOpen) return;

    const stats: EngineDiagnostics = Diagnostics.getStats(engine);

    if (this.statBackend) this.statBackend.textContent = stats.activeBackend;
    if (this.statFps) this.statFps.textContent = `${stats.fps} (min: ${stats.minFps}, max: ${stats.maxFps})`;
    if (this.statFrameTime) this.statFrameTime.textContent = `${stats.frameTimeMs} ms`;
    if (this.statCalls) this.statCalls.textContent = `${stats.drawCalls}`;
    if (this.statTriangles) this.statTriangles.textContent = `${stats.triangles.toLocaleString()}`;
    if (this.statMemory) {
      this.statMemory.textContent = stats.memoryMB !== null ? `${stats.memoryMB} MB` : 'N/A';
    }

    if (this.statPlayerPos) {
      const px = Math.round(player.position.x * 10) / 10;
      const py = Math.round(player.position.y * 10) / 10;
      const pz = Math.round(player.position.z * 10) / 10;
      this.statPlayerPos.textContent = `X: ${px}, Y: ${py}, Z: ${pz}`;
    }

    if (this.statPlayerSpeed) {
      const spd = Math.round(Math.hypot(player.velocity.x, player.velocity.z) * 10) / 10;
      this.statPlayerSpeed.textContent = `${spd} m/s (${player.state})`;
    }

    if (this.statPlayerGround) {
      const g = player.groundContact;
      const groundState = g.isGrounded ? (g.isWalkable ? 'Grounded' : 'Sliding') : 'Airborne';
      this.statPlayerGround.textContent = `${groundState} (${g.slopeAngleDeg}°)`;
    }

    if (this.statCameraPos) {
      this.statCameraPos.textContent = `X: ${stats.cameraPos.x}, Y: ${stats.cameraPos.y}, Z: ${stats.cameraPos.z}`;
    }

    // Update World Streaming & Geography Telemetry
    if (scene && scene.streamer) {
      const telem = scene.streamer.getTelemetry();
      const region = elevationSampler.getNearestRegion(player.position.x, player.position.z);

      if (this.statStreamRegion) {
        this.statStreamRegion.textContent = `${region.name} (${region.biome})`;
      }
      if (this.statStreamChunk) {
        this.statStreamChunk.textContent = `${telem.playerChunk.cx}, ${telem.playerChunk.cz}`;
      }
      if (this.statStreamActive) {
        this.statStreamActive.textContent = `${telem.activeChunksCount} (L0:${telem.lod0Count} / L1:${telem.lod1Count} / L2:${telem.lod2Count})`;
      }
      if (this.statStreamQueue) {
        this.statStreamQueue.textContent = `${telem.queueLength} queued`;
      }
      if (this.statStreamLoaded) {
        this.statStreamLoaded.textContent = `${telem.totalLoaded} / ${telem.totalUnloaded}`;
      }
    }
  }
}
