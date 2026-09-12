import * as THREE from 'three';
import { HumanoidMesh, LocomotionState } from './HumanoidMesh';
import { input } from '../core/InputManager';

export interface GroundContactInfo {
  isGrounded: boolean;
  groundHeight: number;
  normal: THREE.Vector3;
  slopeAngleDeg: number;
  isWalkable: boolean;
}

export class CharacterController {
  public mesh: HumanoidMesh;
  public position: THREE.Vector3 = new THREE.Vector3(0, 0, 0);
  public velocity: THREE.Vector3 = new THREE.Vector3(0, 0, 0);
  public facingAngle: number = 0;
  public state: LocomotionState = 'idle';

  // Capsule Specs
  public readonly capsuleRadius: number = 0.35;
  public readonly standHeight: number = 1.8;
  public readonly crouchHeight: number = 1.15;
  public currentHeight: number = 1.8;

  // Locomotion Tuning
  private readonly walkSpeed: number = 5.0;
  private readonly sprintSpeed: number = 9.8;
  private readonly crouchSpeed: number = 2.4;
  private readonly acceleration: number = 45.0;
  private readonly deceleration: number = 38.0;
  private readonly airAcceleration: number = 15.0;
  private readonly jumpForce: number = 8.5;
  private readonly gravity: number = 22.0;
  private readonly maxStepHeight: number = 0.35;
  private readonly maxSlopeAngleDeg: number = 46.0;

  // Ground Status
  public groundContact: GroundContactInfo = {
    isGrounded: true,
    groundHeight: 0,
    normal: new THREE.Vector3(0, 1, 0),
    slopeAngleDeg: 0,
    isWalkable: true,
  };

  // Environment Collision Objects (passed from scene)
  public colliders: THREE.Object3D[] = [];

  // Raycaster Pool
  private downRaycaster: THREE.Raycaster = new THREE.Raycaster();
  private fwdRaycaster: THREE.Raycaster = new THREE.Raycaster();
  private upRaycaster: THREE.Raycaster = new THREE.Raycaster();

  constructor() {
    this.mesh = new HumanoidMesh();
    this.mesh.group.position.copy(this.position);
  }

  public update(dt: number, cameraYaw: number): void {
    const inputState = input.getState();

    // 1. Ground & Slope Probing
    this.evaluateGround();

    // 2. Crouch State & Ceiling Check
    const wantsCrouch = inputState.crouch;
    if (wantsCrouch) {
      this.currentHeight = THREE.MathUtils.lerp(this.currentHeight, this.crouchHeight, Math.min(1.0, dt * 12));
    } else {
      // Check ceiling clearance before uncrouching
      if (!this.checkCeilingObstruction()) {
        this.currentHeight = THREE.MathUtils.lerp(this.currentHeight, this.standHeight, Math.min(1.0, dt * 12));
      }
    }
    const isCrouching = this.currentHeight < 1.45;

    // 3. Movement Direction relative to Camera
    let moveX = 0;
    let moveZ = 0;
    if (inputState.forward) moveZ -= 1;
    if (inputState.backward) moveZ += 1;
    if (inputState.left) moveX -= 1;
    if (inputState.right) moveX += 1;

    const inputMag = Math.hypot(moveX, moveZ);
    let targetSpeed = 0;

    if (inputMag > 0.01) {
      if (isCrouching) {
        targetSpeed = this.crouchSpeed;
      } else if (inputState.sprint) {
        targetSpeed = this.sprintSpeed;
      } else {
        targetSpeed = this.walkSpeed;
      }
    }

    // Camera alignment
    let desiredWorldDir = new THREE.Vector3(0, 0, 0);
    if (inputMag > 0.01) {
      const normX = moveX / inputMag;
      const normZ = moveZ / inputMag;

      const cosY = Math.cos(cameraYaw);
      const sinY = Math.sin(cameraYaw);

      desiredWorldDir.x = normX * cosY - normZ * sinY;
      desiredWorldDir.z = normX * sinY + normZ * cosY;

      // Project desired movement along walkable slope plane
      if (this.groundContact.isGrounded && this.groundContact.isWalkable) {
        const slopeTangent = new THREE.Vector3();
        slopeTangent.crossVectors(this.groundContact.normal, desiredWorldDir).cross(this.groundContact.normal).normalize();
        desiredWorldDir.copy(slopeTangent);
      }

      // Smooth Character Facing Rotation
      const targetFacing = Math.atan2(desiredWorldDir.x, desiredWorldDir.z);
      this.facingAngle = THREE.MathUtils.lerp(this.facingAngle, targetFacing, Math.min(1.0, dt * 18));
    }

    // 4. Horizontal Acceleration & Deceleration
    const currentAccel = this.groundContact.isGrounded ? this.acceleration : this.airAcceleration;
    const targetVelX = desiredWorldDir.x * targetSpeed;
    const targetVelZ = desiredWorldDir.z * targetSpeed;

    if (inputMag > 0.01) {
      this.velocity.x = THREE.MathUtils.lerp(this.velocity.x, targetVelX, Math.min(1.0, dt * (currentAccel / 5)));
      this.velocity.z = THREE.MathUtils.lerp(this.velocity.z, targetVelZ, Math.min(1.0, dt * (currentAccel / 5)));
    } else {
      // Crisp Braking
      const brakeFactor = Math.min(1.0, dt * (this.deceleration / 3));
      this.velocity.x = THREE.MathUtils.lerp(this.velocity.x, 0, brakeFactor);
      this.velocity.z = THREE.MathUtils.lerp(this.velocity.z, 0, brakeFactor);
    }

    // 5. Jump Execution
    if (inputState.jump && this.groundContact.isGrounded && !isCrouching && this.groundContact.isWalkable) {
      this.velocity.y = this.jumpForce;
      this.groundContact.isGrounded = false;
    }

    // 6. Gravity & Vertical Physics
    if (!this.groundContact.isGrounded) {
      this.velocity.y = Math.max(-32.0, this.velocity.y - this.gravity * dt);
    } else {
      if (this.groundContact.slopeAngleDeg > this.maxSlopeAngleDeg) {
        // Too steep! Slide downward along slope gradient
        const slideDir = new THREE.Vector3(this.groundContact.normal.x, 0, this.groundContact.normal.z).normalize();
        this.velocity.x += slideDir.x * 16.0 * dt;
        this.velocity.z += slideDir.z * 16.0 * dt;
        this.velocity.y -= 10.0 * dt;
      }
    }

    // 7. Stair Step-Up Check (before position translation)
    if (inputMag > 0.01 && this.groundContact.isGrounded) {
      this.checkStairStepUp(desiredWorldDir);
    }

    // 8. Integrate Position
    this.position.x += this.velocity.x * dt;
    this.position.y += this.velocity.y * dt;
    this.position.z += this.velocity.z * dt;

    // Ground Snapping
    if (this.position.y <= this.groundContact.groundHeight) {
      this.position.y = this.groundContact.groundHeight;
      this.velocity.y = 0;
      this.groundContact.isGrounded = true;
    }

    // 9. Update Mesh Transform & Animation State
    this.mesh.group.position.copy(this.position);
    this.mesh.group.rotation.y = this.facingAngle;

    const horizontalSpeed = Math.hypot(this.velocity.x, this.velocity.z);

    if (!this.groundContact.isGrounded) {
      this.state = this.velocity.y > 0 ? 'jump' : 'fall';
    } else if (isCrouching) {
      this.state = 'crouch';
    } else if (horizontalSpeed > 6.0) {
      this.state = 'sprint';
    } else if (horizontalSpeed > 0.2) {
      this.state = 'walk';
    } else {
      this.state = 'idle';
    }

    this.mesh.animate(this.state, horizontalSpeed, dt);
  }

  private evaluateGround(): void {
    let bestGroundY = 0;
    let normal = new THREE.Vector3(0, 1, 0);
    let hitFound = false;

    // Multi-point downward raycasting (center + 4 perimeter points)
    const offsets = [
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(this.capsuleRadius * 0.7, 0, 0),
      new THREE.Vector3(-this.capsuleRadius * 0.7, 0, 0),
      new THREE.Vector3(0, 0, this.capsuleRadius * 0.7),
      new THREE.Vector3(0, 0, -this.capsuleRadius * 0.7),
    ];

    const probeStartY = this.position.y + 0.6;
    const probeDist = 1.4;

    for (const off of offsets) {
      const origin = new THREE.Vector3(
        this.position.x + off.x,
        probeStartY,
        this.position.z + off.z
      );

      this.downRaycaster.set(origin, new THREE.Vector3(0, -1, 0));
      this.downRaycaster.far = probeDist;

      const hits = this.downRaycaster.intersectObjects(this.colliders, true);
      if (hits.length > 0) {
        const hit = hits[0];
        if (hit.point.y > bestGroundY || !hitFound) {
          bestGroundY = hit.point.y;
          if (hit.normal) normal.copy(hit.normal);
          hitFound = true;
        }
      }
    }

    // Default ground level at y = 0
    if (!hitFound) {
      bestGroundY = 0;
      normal.set(0, 1, 0);
    }

    const slopeAngleRad = Math.acos(Math.max(-1, Math.min(1, normal.y)));
    const slopeAngleDeg = (slopeAngleRad * 180) / Math.PI;

    this.groundContact.groundHeight = bestGroundY;
    this.groundContact.normal.copy(normal);
    this.groundContact.slopeAngleDeg = Math.round(slopeAngleDeg * 10) / 10;
    this.groundContact.isWalkable = slopeAngleDeg <= this.maxSlopeAngleDeg;
    this.groundContact.isGrounded = Math.abs(this.position.y - bestGroundY) < 0.15;
  }

  private checkStairStepUp(moveDir: THREE.Vector3): void {
    if (this.colliders.length === 0) return;

    // 1. Low probe at foot level
    const footOrigin = new THREE.Vector3(this.position.x, this.position.y + 0.08, this.position.z);
    this.fwdRaycaster.set(footOrigin, moveDir);
    this.fwdRaycaster.far = this.capsuleRadius + 0.3;

    const lowHits = this.fwdRaycaster.intersectObjects(this.colliders, true);
    if (lowHits.length === 0) return;

    // 2. High probe at maxStepHeight
    const stepTopOrigin = new THREE.Vector3(this.position.x, this.position.y + this.maxStepHeight + 0.05, this.position.z);
    this.fwdRaycaster.set(stepTopOrigin, moveDir);
    this.fwdRaycaster.far = this.capsuleRadius + 0.35;

    const highHits = this.fwdRaycaster.intersectObjects(this.colliders, true);
    // If high probe is unobstructed, a walkable step exists!
    if (highHits.length === 0) {
      // Cast downward probe onto the step tread
      const stepProbeOrigin = new THREE.Vector3(
        this.position.x + moveDir.x * (this.capsuleRadius + 0.25),
        this.position.y + this.maxStepHeight + 0.1,
        this.position.z + moveDir.z * (this.capsuleRadius + 0.25)
      );

      this.downRaycaster.set(stepProbeOrigin, new THREE.Vector3(0, -1, 0));
      this.downRaycaster.far = this.maxStepHeight + 0.2;

      const treadHits = this.downRaycaster.intersectObjects(this.colliders, true);
      if (treadHits.length > 0) {
        const stepTargetY = treadHits[0].point.y;
        const heightDiff = stepTargetY - this.position.y;
        if (heightDiff > 0.04 && heightDiff <= this.maxStepHeight) {
          // Smoothly boost player onto the stair step
          this.position.y = THREE.MathUtils.lerp(this.position.y, stepTargetY, 0.5);
          this.velocity.y = 0;
          this.groundContact.isGrounded = true;
        }
      }
    }
  }

  private checkCeilingObstruction(): boolean {
    if (this.colliders.length === 0) return false;

    // Upward raycast from current crouch height to full stand height
    const origin = new THREE.Vector3(this.position.x, this.position.y + this.crouchHeight, this.position.z);
    this.upRaycaster.set(origin, new THREE.Vector3(0, 1, 0));
    this.upRaycaster.far = this.standHeight - this.crouchHeight + 0.15;

    const hits = this.upRaycaster.intersectObjects(this.colliders, true);
    return hits.length > 0;
  }

  public getLookTarget(): THREE.Vector3 {
    // Focus target for third-person camera: tracks head/chest height smoothly
    const targetHeight = this.currentHeight * 0.82;
    return new THREE.Vector3(this.position.x, this.position.y + targetHeight, this.position.z);
  }

  public setWireframe(wireframe: boolean): void {
    this.mesh.setWireframe(wireframe);
  }

  public dispose(): void {
    this.mesh.dispose();
  }
}
