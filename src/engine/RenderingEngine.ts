import * as THREE from 'three';
import { settings, GraphicsSettings } from '../core/SettingsManager';

export type RendererBackendType = 'WebGPU' | 'WebGL2 (Fallback)';

export class RenderingEngine {
  public renderer!: THREE.WebGLRenderer;
  public camera: THREE.PerspectiveCamera;
  public container: HTMLElement;
  public activeBackend: RendererBackendType = 'WebGL2 (Fallback)';
  public isInitialized: boolean = false;

  private boundResize: () => void;
  private settingsUnsubscribe?: () => void;

  constructor(container: HTMLElement) {
    this.container = container;

    // Perspective Camera setup
    const aspect = container.clientWidth / (container.clientHeight || 1);
    this.camera = new THREE.PerspectiveCamera(settings.settings.fov, aspect, 0.1, 1000);
    this.camera.position.set(0, 5, 10);

    this.boundResize = this.onResize.bind(this);
  }

  public async init(): Promise<void> {
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;

    let webgpuSuccess = false;

    // 1. Attempt WebGPU initialization if supported by browser/GPU
    if (typeof navigator !== 'undefined' && 'gpu' in navigator && (navigator as any).gpu) {
      try {
        console.log('🔍 WebGPU detected in navigator.gpu, attempting WebGPURenderer initialization...');
        const WebGPU = await import('three/webgpu');
        if (WebGPU && WebGPU.WebGPURenderer) {
          const gpuRenderer = new WebGPU.WebGPURenderer({
            antialias: true,
            powerPreference: 'high-performance',
          });
          // WebGPURenderer.init() initializes the adapter and device
          await (gpuRenderer as any).init();
          this.renderer = gpuRenderer as unknown as THREE.WebGLRenderer;
          this.activeBackend = 'WebGPU';
          webgpuSuccess = true;
          console.log('🚀 WebGPU Renderer Initialized Successfully!');
        }
      } catch (err) {
        console.warn('⚠️ WebGPU initialization failed or unsupported on this device. Falling back to WebGL2:', err);
        webgpuSuccess = false;
      }
    }

    // 2. WebGL2 Fallback Path
    if (!webgpuSuccess) {
      console.log('⚡ Initializing WebGL2 Fallback Renderer...');
      this.renderer = new THREE.WebGLRenderer({
        antialias: true,
        powerPreference: 'high-performance',
        stencil: false,
        depth: true,
      });
      this.activeBackend = 'WebGL2 (Fallback)';
      console.log('✅ WebGL2 Fallback Renderer Initialized Successfully');
    }

    // Configure common renderer properties
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, settings.settings.maxPixelRatio));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;

    // Shadows (using modern PCFShadowMap in Three.js)
    if (this.renderer.shadowMap) {
      this.renderer.shadowMap.enabled = settings.settings.shadows;
      this.renderer.shadowMap.type = THREE.PCFShadowMap;
    }

    // Mount canvas into DOM
    this.renderer.domElement.style.width = '100%';
    this.renderer.domElement.style.height = '100%';
    this.renderer.domElement.style.display = 'block';
    this.container.innerHTML = '';
    this.container.appendChild(this.renderer.domElement);

    // Bind event listeners
    window.addEventListener('resize', this.boundResize);

    // Bind settings changes
    this.settingsUnsubscribe = settings.onChange((newSettings) => {
      this.applySettings(newSettings);
    });

    this.isInitialized = true;
  }

  public applySettings(s: GraphicsSettings): void {
    if (!this.renderer) return;

    if (this.renderer.shadowMap) {
      this.renderer.shadowMap.enabled = s.shadows;
    }
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, s.maxPixelRatio));

    if (this.camera.fov !== s.fov) {
      this.camera.fov = s.fov;
      this.camera.updateProjectionMatrix();
    }
  }

  public onResize(): void {
    if (!this.container || !this.renderer) return;
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;

    this.camera.aspect = width / (height || 1);
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, settings.settings.maxPixelRatio));
  }

  public fallbackToWebGL(scene?: THREE.Scene): void {
    console.warn('⚡ Switching to WebGL2 Fallback Renderer...');
    if (this.renderer) {
      this.renderer.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentElement) {
        this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
      }
    }

    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
      stencil: false,
      depth: true,
    });
    this.activeBackend = 'WebGL2 (Fallback)';

    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, settings.settings.maxPixelRatio));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;

    if (this.renderer.shadowMap) {
      this.renderer.shadowMap.enabled = settings.settings.shadows;
      this.renderer.shadowMap.type = THREE.PCFShadowMap;
    }

    this.renderer.domElement.style.width = '100%';
    this.renderer.domElement.style.height = '100%';
    this.renderer.domElement.style.display = 'block';
    this.container.appendChild(this.renderer.domElement);

    if (scene) {
      this.renderer.render(scene, this.camera);
    }
  }

  public render(scene: THREE.Scene): void {
    if (!this.isInitialized || !this.renderer) return;
    try {
      this.renderer.render(scene, this.camera);
    } catch (err) {
      if (this.activeBackend === 'WebGPU') {
        console.warn('⚠️ WebGPU runtime render error encountered. Automatically switching to WebGL2 Fallback:', err);
        this.fallbackToWebGL(scene);
      } else {
        console.error('Render error:', err);
      }
    }
  }

  public dispose(): void {
    window.removeEventListener('resize', this.boundResize);
    if (this.settingsUnsubscribe) {
      this.settingsUnsubscribe();
    }

    if (this.renderer) {
      this.renderer.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentElement) {
        this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
      }
    }
    this.isInitialized = false;
  }
}
