import * as THREE from 'three';
import { Ground } from './Ground';
import { Sky } from './Sky';
import { Lighting } from './Lighting';
import { CharacterController } from '../player/CharacterController';
import { GymEnvironment } from './GymEnvironment';
import { WorldStreamer } from '../streaming/WorldStreamer';
import { settings } from '../core/SettingsManager';

export class TestScene {
  public scene: THREE.Scene;
  public ground: Ground;
  public sky: Sky;
  public lighting: Lighting;
  public player: CharacterController;
  public gym: GymEnvironment;
  public streamer: WorldStreamer;

  public allColliders: THREE.Object3D[] = [];
  private settingsUnsubscribe: () => void;

  constructor() {
    this.scene = new THREE.Scene();

    // 1. Sky
    this.sky = new Sky();
    this.scene.add(this.sky.mesh);

    // 2. Lighting
    this.lighting = new Lighting();
    this.scene.add(this.lighting.group);

    // 3. Central Training Ground Pad
    this.ground = new Ground(160);
    this.scene.add(this.ground.mesh);

    // 4. Gym Environment (Obstacle testing course in central hub)
    this.gym = new GymEnvironment();
    this.scene.add(this.gym.group);

    // 5. Coordinate-Based World Streamer
    this.streamer = new WorldStreamer(this.scene, {
      chunkSize: 200,
      lod0Radius: 1, // 3x3 inner collision window
      lod1Radius: 2, // 5x5 mid visual window
      lod2Radius: 4, // 9x9 outer proxy horizon
      maxBuildsPerFrame: 2,
    });

    // 6. Aggregate Colliders for Character & Camera
    this.refreshColliders();

    // 7. Character Controller
    this.player = new CharacterController();
    this.player.colliders = this.allColliders;
    this.player.position.set(0, 0, 0);
    this.scene.add(this.player.mesh.group);

    // Wire up settings changes
    this.settingsUnsubscribe = settings.onChange((s) => {
      this.lighting.setShadows(s.shadows);
      this.ground.setWireframe(s.wireframe);
      this.gym.setWireframe(s.wireframe);
      this.player.setWireframe(s.wireframe);
      for (const chunk of this.streamer.activeChunks.values()) {
        // Wireframe toggle propagates to chunks
      }
    });
  }

  public refreshColliders(): void {
    this.allColliders.length = 0;
    this.allColliders.push(this.ground.mesh);
    this.allColliders.push(...this.gym.colliders);
    this.allColliders.push(...this.streamer.allChunkColliders);
  }

  public update(dt: number, cameraYaw: number): void {
    // Update player locomotion & physics
    this.player.update(dt, cameraYaw);

    // Update coordinate-based world streaming based on player position and velocity
    this.streamer.update(this.player.position, this.player.velocity);

    // Sync streaming colliders
    this.refreshColliders();
    this.player.colliders = this.allColliders;
  }

  public dispose(): void {
    this.settingsUnsubscribe();
    this.ground.dispose();
    this.sky.dispose();
    this.lighting.dispose();
    this.gym.dispose();
    this.streamer.dispose();
    this.player.dispose();

    while (this.scene.children.length > 0) {
      this.scene.remove(this.scene.children[0]);
    }
  }
}
