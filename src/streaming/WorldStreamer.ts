import * as THREE from 'three';
import { WorldChunk } from './WorldChunk';
import { ChunkCoord, chunkCoordKey } from '../world/types';

export interface StreamerConfig {
  chunkSize: number;
  lod0Radius: number; // High detail with collision
  lod1Radius: number; // Mid detail visual
  lod2Radius: number; // Low detail proxy mesh
  maxBuildsPerFrame: number; // Budget per frame to prevent stutter
}

interface QueuedChunkTask {
  cx: number;
  cz: number;
  lod: number;
  priority: number;
}

export interface StreamingTelemetry {
  playerChunk: ChunkCoord;
  activeChunksCount: number;
  lod0Count: number;
  lod1Count: number;
  lod2Count: number;
  queueLength: number;
  totalLoaded: number;
  totalUnloaded: number;
}

export class WorldStreamer {
  public config: StreamerConfig;
  public parentScene: THREE.Scene;
  public activeChunks: Map<string, WorldChunk> = new Map();
  public allChunkColliders: THREE.Object3D[] = [];

  // Telemetry metrics
  public totalLoaded: number = 0;
  public totalUnloaded: number = 0;
  private currentCenterChunk: ChunkCoord = { cx: 999999, cz: 999999 };

  // Background Priority Queue
  private loadQueue: QueuedChunkTask[] = [];
  private queuedKeys: Set<string> = new Set();

  constructor(scene: THREE.Scene, customConfig?: Partial<StreamerConfig>) {
    this.parentScene = scene;
    this.config = {
      chunkSize: 200,
      lod0Radius: 1, // 3x3 inner collision window
      lod1Radius: 2, // 5x5 mid visual window
      lod2Radius: 4, // 9x9 outer proxy horizon
      maxBuildsPerFrame: 2,
      ...customConfig,
    };
  }

  public update(playerPos: THREE.Vector3, playerVelocity: THREE.Vector3): void {
    const cx = Math.floor(playerPos.x / this.config.chunkSize);
    const cz = Math.floor(playerPos.z / this.config.chunkSize);

    // If player crosses into a new chunk or on initial boot
    if (cx !== this.currentCenterChunk.cx || cz !== this.currentCenterChunk.cz) {
      this.currentCenterChunk = { cx, cz };
      this.recalculateStreaming(cx, cz, playerVelocity);
    }

    // Process asynchronous background load queue within frame budget
    this.processLoadQueue();
  }

  private recalculateStreaming(centerCx: number, centerCz: number, playerVel: THREE.Vector3): void {
    const requiredKeys = new Map<string, number>(); // key -> target LOD

    // Normalized player heading direction for priority calculation
    const velMag = Math.hypot(playerVel.x, playerVel.z);
    const headingDir = velMag > 0.1
      ? new THREE.Vector2(playerVel.x / velMag, playerVel.z / velMag)
      : new THREE.Vector2(0, 1);

    const maxR = this.config.lod2Radius;

    for (let dx = -maxR; dx <= maxR; dx++) {
      for (let dz = -maxR; dz <= maxR; dz++) {
        const distSq = dx * dx + dz * dz;
        const dist = Math.sqrt(distSq);

        if (dist > maxR + 0.1) continue;

        const cx = centerCx + dx;
        const cz = centerCz + dz;
        const key = chunkCoordKey(cx, cz);

        // Determine appropriate LOD
        let targetLod = 2;
        if (dist <= this.config.lod0Radius + 0.2) {
          targetLod = 0;
        } else if (dist <= this.config.lod1Radius + 0.2) {
          targetLod = 1;
        }

        requiredKeys.set(key, targetLod);

        // If chunk is already active:
        const existing = this.activeChunks.get(key);
        if (existing) {
          if (existing.lodLevel !== targetLod) {
            // LOD transition needed
            this.enqueueChunk(cx, cz, targetLod, 10);
          }
        } else if (!this.queuedKeys.has(key)) {
          // Calculate directional loading priority
          // Chunks ahead of player heading get higher priority score
          const chunkDir = new THREE.Vector2(dx, dz).normalize();
          const dot = chunkDir.dot(headingDir); // 1 = directly ahead, -1 = behind
          // Closer chunks and chunks in front get highest priority
          const priority = (1.0 - dist / (maxR + 1)) * 100 + (dot + 1) * 20;

          this.enqueueChunk(cx, cz, targetLod, priority);
        }
      }
    }

    // Unload distant chunks outside streaming radius
    for (const [key, chunk] of this.activeChunks.entries()) {
      if (!requiredKeys.has(key)) {
        this.unloadChunk(key, chunk);
      }
    }

    // Clean up queue of any tasks that are no longer required
    this.loadQueue = this.loadQueue.filter((task) => {
      const k = chunkCoordKey(task.cx, task.cz);
      const isReq = requiredKeys.has(k);
      if (!isReq) this.queuedKeys.delete(k);
      return isReq;
    });
  }

  private enqueueChunk(cx: number, cz: number, lod: number, priority: number): void {
    const key = chunkCoordKey(cx, cz);
    this.queuedKeys.add(key);

    // Insert sorted by priority descending
    const task: QueuedChunkTask = { cx, cz, lod, priority };
    const idx = this.loadQueue.findIndex((t) => t.priority < priority);
    if (idx === -1) {
      this.loadQueue.push(task);
    } else {
      this.loadQueue.splice(idx, 0, task);
    }
  }

  private processLoadQueue(): void {
    let buildsThisFrame = 0;

    while (this.loadQueue.length > 0 && buildsThisFrame < this.config.maxBuildsPerFrame) {
      const task = this.loadQueue.shift()!;
      const key = chunkCoordKey(task.cx, task.cz);
      this.queuedKeys.delete(key);

      const existing = this.activeChunks.get(key);
      if (existing) {
        // Rebuild LOD
        existing.buildChunk(task.lod);
      } else {
        // Build new chunk
        const chunk = new WorldChunk({ cx: task.cx, cz: task.cz }, this.config.chunkSize, task.lod);
        this.parentScene.add(chunk.group);
        this.activeChunks.set(key, chunk);
        this.totalLoaded++;
      }

      buildsThisFrame++;
    }

    // Refresh aggregated colliders list if any chunks changed
    if (buildsThisFrame > 0) {
      this.rebuildCollidersList();
    }
  }

  private unloadChunk(key: string, chunk: WorldChunk): void {
    chunk.dispose();
    this.activeChunks.delete(key);
    this.totalUnloaded++;
    this.rebuildCollidersList();
  }

  private rebuildCollidersList(): void {
    this.allChunkColliders.length = 0;
    for (const chunk of this.activeChunks.values()) {
      if (chunk.lodLevel === 0) {
        this.allChunkColliders.push(...chunk.colliders);
      }
    }
  }

  public getTelemetry(): StreamingTelemetry {
    let lod0 = 0;
    let lod1 = 0;
    let lod2 = 0;

    for (const chunk of this.activeChunks.values()) {
      if (chunk.lodLevel === 0) lod0++;
      else if (chunk.lodLevel === 1) lod1++;
      else lod2++;
    }

    return {
      playerChunk: { ...this.currentCenterChunk },
      activeChunksCount: this.activeChunks.size,
      lod0Count: lod0,
      lod1Count: lod1,
      lod2Count: lod2,
      queueLength: this.loadQueue.length,
      totalLoaded: this.totalLoaded,
      totalUnloaded: this.totalUnloaded,
    };
  }

  public dispose(): void {
    this.loadQueue.length = 0;
    this.queuedKeys.clear();

    for (const chunk of this.activeChunks.values()) {
      chunk.dispose();
    }
    this.activeChunks.clear();
    this.allChunkColliders.length = 0;
  }
}
