export class Time {
  public static delta: number = 0;
  public static elapsed: number = 0;
  public static timeScale: number = 1.0;
  public static frameCount: number = 0;
  public static fps: number = 60;
  public static frameTimeMs: number = 16.6;
  public static minFps: number = 60;
  public static maxFps: number = 60;

  private static lastTime: number = performance.now();
  private static fpsAccumulator: number = 0;
  private static fpsFrames: number = 0;

  public static update(): void {
    const now = performance.now();
    const rawDelta = (now - this.lastTime) / 1000;
    this.lastTime = now;

    this.frameTimeMs = Math.round(rawDelta * 1000 * 10) / 10;

    // Clamp delta to prevent physics explosion during tab switch
    this.delta = Math.min(rawDelta, 0.1) * this.timeScale;
    this.elapsed += this.delta;
    this.frameCount++;

    // Calculate moving average FPS
    this.fpsAccumulator += rawDelta;
    this.fpsFrames++;
    if (this.fpsAccumulator >= 0.5) {
      const currentFps = Math.round(this.fpsFrames / this.fpsAccumulator);
      this.fps = currentFps;
      this.minFps = Math.min(this.minFps, currentFps);
      this.maxFps = Math.max(this.maxFps, currentFps);
      this.fpsAccumulator = 0;
      this.fpsFrames = 0;
    }
  }

  public static reset(): void {
    this.lastTime = performance.now();
    this.delta = 0;
    this.elapsed = 0;
    this.frameCount = 0;
    this.minFps = 60;
    this.maxFps = 60;
  }
}
