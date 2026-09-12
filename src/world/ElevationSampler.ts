import * as THREE from 'three';
import { ElevationProvider, RegionalDefinition } from './types';
import { TAMIL_NADU_REGIONS } from './TamilNaduDataset';

export class ElevationSampler implements ElevationProvider {
  private static instance: ElevationSampler;
  private perm: number[] = [];
  private initialized: boolean = false;

  constructor() {
    this.initNoise();
  }

  public static getInstance(): ElevationSampler {
    if (!ElevationSampler.instance) {
      ElevationSampler.instance = new ElevationSampler();
    }
    return ElevationSampler.instance;
  }

  private initNoise(): void {
    if (this.initialized) return;
    const p: number[] = [];
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) {
      const r = Math.floor(Math.sin(i * 12.9898 + 78.233) * 43758.5453) & 255;
      const swap: number = p[i];
      p[i] = p[r];
      p[r] = swap;
    }
    for (let i = 0; i < 512; i++) {
      this.perm[i] = p[i & 255];
    }
    this.initialized = true;
  }

  private grad(hash: number, x: number, y: number): number {
    const h = hash & 7;
    const u = h < 4 ? x : y;
    const v = h < 4 ? y : x;
    return (h & 1 ? -u : u) + (h & 2 ? -2.0 * v : 2.0 * v);
  }

  public noise2D(x: number, y: number): number {
    const xi = Math.floor(x) & 255;
    const yi = Math.floor(y) & 255;
    const xf = x - Math.floor(x);
    const yf = y - Math.floor(y);

    const u = xf * xf * (3.0 - 2.0 * xf);
    const v = yf * yf * (3.0 - 2.0 * yf);

    const aa = this.perm[this.perm[xi] + yi];
    const ab = this.perm[this.perm[xi] + yi + 1];
    const ba = this.perm[this.perm[xi + 1] + yi];
    const bb = this.perm[this.perm[xi + 1] + yi + 1];

    const x1 = (1 - u) * this.grad(aa, xf, yf) + u * this.grad(ba, xf - 1, yf);
    const x2 = (1 - u) * this.grad(ab, xf, yf - 1) + u * this.grad(bb, xf - 1, yf - 1);

    return (1 - v) * x1 + v * x2;
  }

  public getElevation(x: number, z: number): number {
    // 1. Regional Macro Elevation Map
    let base = 20.0;

    // Nilgiris & Western Ghats (West: X < -500)
    if (x < -500) {
      const westFactor = Math.min(1.0, (-x - 500) / 450);
      const mountainNoise = Math.abs(this.noise2D(x * 0.003, z * 0.003)) * 130;
      const ridgeNoise = Math.abs(this.noise2D(x * 0.008, z * 0.008)) * 50;
      base += westFactor * (100 + mountainNoise + ridgeNoise);
    }

    // Eastern Coastline & Bay of Bengal (East: X > 450)
    if (x > 450) {
      const coastFactor = (x - 450) / 250;
      base = Math.max(-10, base * (1.0 - coastFactor));
      if (x > 720) return -12; // Ocean floor
    }

    // Southern Coastline & Indian Ocean (South: Z > 850)
    if (z > 850) {
      const southFactor = (z - 850) / 250;
      base = Math.max(-10, base * (1.0 - southFactor));
      if (z > 1080) return -12;
    }

    // Trichy Rockfort Monolithic Inselberg (X: 50, Z: -500)
    const dRockfort = Math.hypot(x - 50, z + 500);
    if (dRockfort < 80) {
      const rf = Math.cos((dRockfort / 80) * (Math.PI / 2));
      base += rf * rf * 80;
    }

    // Kaveri River Channel
    const kaveriZ = -500 + Math.sin(x * 0.004) * 45;
    const distKaveri = Math.abs(z - kaveriZ);
    if (distKaveri < 60 && x > -500 && x < 680) {
      const riverDepth = (1.0 - distKaveri / 60) * 10;
      base -= riverDepth;
    }

    // Micro and meso natural undulation
    const n1 = this.noise2D(x * 0.002, z * 0.002) * 16;
    const n2 = this.noise2D(x * 0.007, z * 0.007) * 5;

    return base + n1 + n2;
  }

  public getNormal(x: number, z: number, eps: number = 0.5): THREE.Vector3 {
    const hL = this.getElevation(x - eps, z);
    const hR = this.getElevation(x + eps, z);
    const hD = this.getElevation(x, z - eps);
    const hU = this.getElevation(x, z + eps);

    const nx = hL - hR;
    const ny = 2.0 * eps;
    const nz = hD - hU;
    const normal = new THREE.Vector3(nx, ny, nz).normalize();
    return normal;
  }

  public getNearestRegion(x: number, z: number): RegionalDefinition {
    let closest = TAMIL_NADU_REGIONS[0];
    let minDist = Infinity;
    for (const reg of TAMIL_NADU_REGIONS) {
      const dist = Math.hypot(x - reg.center.x, z - reg.center.z);
      if (dist < minDist) {
        minDist = dist;
        closest = reg;
      }
    }
    return closest;
  }
}

export const elevationSampler = ElevationSampler.getInstance();
