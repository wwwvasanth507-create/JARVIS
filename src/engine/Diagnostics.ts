import * as THREE from 'three';
import { Time } from '../core/Time';
import { RenderingEngine } from './RenderingEngine';

export interface EngineDiagnostics {
  fps: number;
  minFps: number;
  maxFps: number;
  frameTimeMs: number;
  activeBackend: string;
  drawCalls: number;
  triangles: number;
  geometries: number;
  textures: number;
  memoryMB: number | null;
  cameraPos: { x: number; y: number; z: number };
}

export class Diagnostics {
  public static getStats(engine: RenderingEngine): EngineDiagnostics {
    let drawCalls = 0;
    let triangles = 0;
    let geometries = 0;
    let textures = 0;

    if (engine.renderer && (engine.renderer as any).info) {
      const info = (engine.renderer as any).info;
      drawCalls = info.render?.calls ?? 0;
      triangles = info.render?.triangles ?? 0;
      geometries = info.memory?.geometries ?? 0;
      textures = info.memory?.textures ?? 0;
    }

    let memoryMB: number | null = null;
    if (typeof performance !== 'undefined' && (performance as any).memory) {
      memoryMB = Math.round(((performance as any).memory.usedJSHeapSize / (1024 * 1024)) * 10) / 10;
    }

    const camPos = engine.camera.position;

    return {
      fps: Time.fps,
      minFps: Time.minFps,
      maxFps: Time.maxFps,
      frameTimeMs: Time.frameTimeMs,
      activeBackend: engine.activeBackend,
      drawCalls,
      triangles,
      geometries,
      textures,
      memoryMB,
      cameraPos: {
        x: Math.round(camPos.x * 10) / 10,
        y: Math.round(camPos.y * 10) / 10,
        z: Math.round(camPos.z * 10) / 10,
      },
    };
  }
}
