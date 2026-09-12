import { RenderingEngine } from '../engine/RenderingEngine';
import { CameraController } from '../engine/CameraController';
import { TestScene } from '../scene/TestScene';
import { GameLoop } from './GameLoop';
import { input } from './InputManager';
import { LoadingScreen } from '../ui/LoadingScreen';
import { FPSCounter } from '../ui/FPSCounter';
import { DebugOverlay } from '../ui/DebugOverlay';

export class Engine {
  public renderer: RenderingEngine;
  public cameraController: CameraController;
  public scene: TestScene;
  public loop: GameLoop;
  public loadingScreen: LoadingScreen;
  public fpsCounter: FPSCounter;
  public debugOverlay: DebugOverlay;

  private isRunning: boolean = false;
  private loopUnsubscribe?: () => void;

  constructor(container: HTMLElement) {
    this.renderer = new RenderingEngine(container);
    this.cameraController = new CameraController(this.renderer.camera);
    this.scene = new TestScene();
    this.loop = new GameLoop();

    // Connect Scene Colliders to Camera for Occlusion Avoidance
    this.cameraController.colliders = this.scene.allColliders;

    // UI Controllers
    this.loadingScreen = new LoadingScreen();
    this.fpsCounter = new FPSCounter();
    this.debugOverlay = new DebugOverlay();

    input.attachToElement(container);
  }

  public async init(): Promise<void> {
    try {
      this.loadingScreen.setProgress(20, 'Detecting WebGPU support...');
      await new Promise((r) => setTimeout(r, 60));

      this.loadingScreen.setProgress(50, 'Initializing 3D Rendering Engine...');
      await this.renderer.init();

      // Update backend badge in UI
      this.fpsCounter.setBackend(this.renderer.activeBackend);

      this.loadingScreen.setProgress(80, 'Constructing test scene & obstacle gym...');
      await new Promise((r) => setTimeout(r, 60));

      // Hook up game loop tick
      this.loopUnsubscribe = this.loop.onTick(this.onTick.bind(this));

      // Pointer lock on canvas click
      this.renderer.renderer.domElement.addEventListener('click', () => {
        input.requestPointerLock();
      });

      this.loadingScreen.setProgress(100, 'Ready!');
      await this.loadingScreen.hide(150);

      this.start();
      console.log(`✨ Engine started successfully. Backend: ${this.renderer.activeBackend}`);
    } catch (err) {
      console.error('Fatal error during engine initialization:', err);
      this.loadingScreen.setProgress(100, 'Initialization failed. Check console.');
      throw err;
    }
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.loop.start();
  }

  public pause(): void {
    this.loop.setPaused(true);
  }

  public resume(): void {
    this.loop.setPaused(false);
  }

  private onTick(dt: number): void {
    // 1. Update Test Scene & Character Controller (physics, slopes, stairs, crouch)
    this.scene.update(dt, this.cameraController.yaw);

    // 2. Camera smoothly follows player look-target with collision avoidance
    this.cameraController.setTarget(this.scene.player.getLookTarget());
    this.cameraController.update();

    // 3. Render 3D Scene
    this.renderer.render(this.scene.scene);

    // 4. Update UI Meters & Diagnostics
    this.fpsCounter.update();
    this.debugOverlay.update(this.renderer, this.scene.player);

    // 5. End Input Frame
    input.endFrame();
  }

  public dispose(): void {
    this.isRunning = false;
    this.loop.stop();

    if (this.loopUnsubscribe) {
      this.loopUnsubscribe();
    }

    this.scene.dispose();
    this.renderer.dispose();
    input.dispose();
  }
}
