import * as THREE from 'three';
import { input } from '../core/InputManager';
import { Time } from '../core/Time';

export class CameraController {
  public camera: THREE.PerspectiveCamera;
  public target: THREE.Vector3 = new THREE.Vector3();

  // Orbit angles & distance
  public yaw: number = 0;
  public pitch: number = 0.25;
  public desiredDistance: number = 5.5;
  public currentDistance: number = 5.5;
  public minDistance: number = 1.2;
  public maxDistance: number = 12.0;
  public minPitch: number = -Math.PI / 8;  // Look slightly down
  public maxPitch: number = Math.PI / 2.3; // Look down from above

  // Smoothing
  public currentPosition: THREE.Vector3 = new THREE.Vector3();
  public lookAtTarget: THREE.Vector3 = new THREE.Vector3();
  public heightOffset: number = 1.35;

  // Collision avoidance
  public colliders: THREE.Object3D[] = [];
  private raycaster: THREE.Raycaster = new THREE.Raycaster();
  private readonly cameraCollisionRadius: number = 0.25;

  constructor(camera: THREE.PerspectiveCamera) {
    this.camera = camera;
    this.currentPosition.copy(camera.position);
    this.lookAtTarget.copy(this.target);
  }

  public update(): void {
    const inputState = input.getState();
    const dt = Time.delta;

    // 1. Mouse Look with Pointer Lock
    const mouseSensitivity = 0.0022;
    if (inputState.isPointerLocked) {
      this.yaw -= inputState.mouseDeltaX * mouseSensitivity;
      this.pitch -= inputState.mouseDeltaY * mouseSensitivity;
      this.pitch = Math.max(this.minPitch, Math.min(this.maxPitch, this.pitch));
    }

    // 2. Mouse Wheel Zoom
    if (inputState.mouseWheel !== 0) {
      this.desiredDistance += inputState.mouseWheel * 0.75;
      this.desiredDistance = Math.max(this.minDistance, Math.min(this.maxDistance, this.desiredDistance));
    }

    // 3. Focus Target
    const desiredLookAt = new THREE.Vector3(
      this.target.x,
      this.target.y,
      this.target.z
    );

    // Compute ideal spherical camera offset
    const cosPitch = Math.cos(this.pitch);
    const sinPitch = Math.sin(this.pitch);
    const sinYaw = Math.sin(this.yaw);
    const cosYaw = Math.cos(this.yaw);

    const cameraDir = new THREE.Vector3(
      cosPitch * sinYaw,
      sinPitch,
      cosPitch * cosYaw
    ).normalize();

    // 4. Camera Collision & Occlusion Raycast
    let targetDist = this.desiredDistance;

    if (this.colliders.length > 0) {
      this.raycaster.set(desiredLookAt, cameraDir);
      this.raycaster.far = this.desiredDistance;

      const hits = this.raycaster.intersectObjects(this.colliders, true);
      if (hits.length > 0) {
        // Hit detected between player and camera! Push camera forward in front of obstacle
        const hitDist = hits[0].distance;
        targetDist = Math.max(this.minDistance, hitDist - this.cameraCollisionRadius);
      }
    }

    // Fast push-in when hitting obstacle, smooth return when clear
    const distLerpSpeed = targetDist < this.currentDistance ? 25.0 : 8.0;
    this.currentDistance = THREE.MathUtils.lerp(this.currentDistance, targetDist, Math.min(1.0, dt * distLerpSpeed));

    const desiredPosition = desiredLookAt.clone().add(
      cameraDir.clone().multiplyScalar(this.currentDistance)
    );

    // 5. Smooth Spring-Arm Following
    const posLerpFactor = Math.min(1.0, dt * 14);
    this.currentPosition.lerp(desiredPosition, posLerpFactor);
    this.lookAtTarget.lerp(desiredLookAt, posLerpFactor);

    this.camera.position.copy(this.currentPosition);
    this.camera.lookAt(this.lookAtTarget);
  }

  public setTarget(pos: THREE.Vector3): void {
    this.target.copy(pos);
  }
}
