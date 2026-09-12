import { Time } from './Time';

export type TickCallback = (dt: number) => void;

export class GameLoop {
  private isRunning: boolean = false;
  private isPaused: boolean = false;
  private animFrameId: number | null = null;
  private tickCallbacks: Set<TickCallback> = new Set();

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.isPaused = false;
    Time.reset();
    this.loop();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.animFrameId !== null) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
  }

  public setPaused(paused: boolean): void {
    this.isPaused = paused;
  }

  public onTick(cb: TickCallback): () => void {
    this.tickCallbacks.add(cb);
    return () => this.tickCallbacks.delete(cb);
  }

  private loop = (): void => {
    if (!this.isRunning) return;
    this.animFrameId = requestAnimationFrame(this.loop);

    Time.update();

    if (!this.isPaused) {
      const dt = Time.delta;
      this.tickCallbacks.forEach((cb) => {
        try {
          cb(dt);
        } catch (err) {
          console.error('Error inside game loop tick:', err);
        }
      });
    }
  };
}
