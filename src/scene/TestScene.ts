import * as THREE from 'three';
import { Ground } from './Ground';
import { Sky } from './Sky';
import { Lighting } from './Lighting';
import { CharacterController } from '../player/CharacterController';
import { GymEnvironment } from './GymEnvironment';
import { settings } from '../core/SettingsManager';

export class TestScene {
  public scene: THREE.Scene;
  public ground: Ground;
  public sky: Sky;
  public lighting: Lighting;
  public player: CharacterController;
  public gym: GymEnvironment;

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

    // 3. Ground
    this.ground = new Ground(160);
    this.scene.add(this.ground.mesh);

    // 4. Gym Environment (Slopes, Stairs, Platforms, Crouch Tunnel, Pillars)
    this.gym = new GymEnvironment();
    this.scene.add(this.gym.group);

    // Aggregate Colliders for Character & Camera
    this.allColliders.push(this.ground.mesh);
    this.allColliders.push(...this.gym.colliders);

    // 5. Character Controller
    this.player = new CharacterController();
    this.player.colliders = this.allColliders;
    // Spawn player in open central area
    this.player.position.set(0, 0, 0);
    this.scene.add(this.player.mesh.group);

    // Wire up settings changes
    this.settingsUnsubscribe = settings.onChange((s) => {
      this.lighting.setShadows(s.shadows);
      this.ground.setWireframe(s.wireframe);
      this.gym.setWireframe(s.wireframe);
      this.player.setWireframe(s.wireframe);
    });
  }

  public update(dt: number, cameraYaw: number): void {
    this.player.update(dt, cameraYaw);
  }

  public dispose(): void {
    this.settingsUnsubscribe();
    this.ground.dispose();
    this.sky.dispose();
    this.lighting.dispose();
    this.gym.dispose();
    this.player.dispose();

    while (this.scene.children.length > 0) {
      this.scene.remove(this.scene.children[0]);
    }
  }
}
