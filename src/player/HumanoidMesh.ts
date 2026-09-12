import * as THREE from 'three';

export type LocomotionState = 'idle' | 'walk' | 'sprint' | 'jump' | 'fall' | 'crouch';

export class HumanoidMesh {
  public group: THREE.Group = new THREE.Group();

  // Rig Hierarchy
  public pelvis: THREE.Group;
  public torso: THREE.Mesh;
  public chest: THREE.Mesh;
  public head: THREE.Group;
  public visor: THREE.Mesh;

  public leftUpperArm: THREE.Group;
  public leftForearm: THREE.Mesh;
  public rightUpperArm: THREE.Group;
  public rightForearm: THREE.Mesh;

  public leftThigh: THREE.Group;
  public leftShin: THREE.Mesh;
  public rightThigh: THREE.Group;
  public rightShin: THREE.Mesh;

  // Shared Materials & Geometries for disposal
  private materials: THREE.Material[] = [];
  private geometries: THREE.BufferGeometry[] = [];

  private animTime: number = 0;
  private currentCrouchBlend: number = 0;

  constructor() {
    // 1. Materials
    const suitMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b, // Slate dark suit
      roughness: 0.4,
      metalness: 0.2,
    });
    const accentMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7, // Bright cyan armor plates
      roughness: 0.25,
      metalness: 0.4,
    });
    const jointMat = new THREE.MeshStandardMaterial({
      color: 0x475569, // Flexible mechanical joints
      roughness: 0.7,
      metalness: 0.1,
    });
    const visorMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8, // Glowing cyan visor
      roughness: 0.1,
      metalness: 0.9,
      emissive: 0x0369a1,
      emissiveIntensity: 0.4,
    });

    this.materials.push(suitMat, accentMat, jointMat, visorMat);

    // 2. Pelvis / Hips Root
    this.pelvis = new THREE.Group();
    this.pelvis.position.y = 0.95; // Standing hip height
    this.group.add(this.pelvis);

    const pelvisGeom = new THREE.BoxGeometry(0.36, 0.18, 0.24);
    this.geometries.push(pelvisGeom);
    const pelvisMesh = new THREE.Mesh(pelvisGeom, jointMat);
    pelvisMesh.castShadow = true;
    this.pelvis.add(pelvisMesh);

    // 3. Torso & Chest
    const torsoGeom = new THREE.BoxGeometry(0.38, 0.28, 0.22);
    this.geometries.push(torsoGeom);
    this.torso = new THREE.Mesh(torsoGeom, suitMat);
    this.torso.position.y = 0.22;
    this.torso.castShadow = true;
    this.pelvis.add(this.torso);

    const chestGeom = new THREE.BoxGeometry(0.44, 0.32, 0.26);
    this.geometries.push(chestGeom);
    this.chest = new THREE.Mesh(chestGeom, accentMat);
    this.chest.position.y = 0.28;
    this.chest.castShadow = true;
    this.torso.add(this.chest);

    // 4. Neck & Head
    this.head = new THREE.Group();
    this.head.position.y = 0.32;
    this.chest.add(this.head);

    const headGeom = new THREE.BoxGeometry(0.24, 0.26, 0.24);
    this.geometries.push(headGeom);
    const headMesh = new THREE.Mesh(headGeom, suitMat);
    headMesh.position.y = 0.13;
    headMesh.castShadow = true;
    this.head.add(headMesh);

    // Visor (Front orientation indicator)
    const visorGeom = new THREE.BoxGeometry(0.22, 0.1, 0.1);
    this.geometries.push(visorGeom);
    this.visor = new THREE.Mesh(visorGeom, visorMat);
    this.visor.position.set(0, 0.13, 0.125);
    this.head.add(this.visor);

    // 5. Left Arm
    this.leftUpperArm = new THREE.Group();
    this.leftUpperArm.position.set(-0.28, 0.12, 0);
    this.chest.add(this.leftUpperArm);

    const armGeom = new THREE.BoxGeometry(0.12, 0.32, 0.12);
    armGeom.translate(0, -0.14, 0);
    this.geometries.push(armGeom);
    const leftBicep = new THREE.Mesh(armGeom, suitMat);
    leftBicep.castShadow = true;
    this.leftUpperArm.add(leftBicep);

    const forearmGeom = new THREE.BoxGeometry(0.1, 0.3, 0.1);
    forearmGeom.translate(0, -0.15, 0);
    this.geometries.push(forearmGeom);
    this.leftForearm = new THREE.Mesh(forearmGeom, accentMat);
    this.leftForearm.position.y = -0.28;
    this.leftForearm.castShadow = true;
    this.leftUpperArm.add(this.leftForearm);

    // 6. Right Arm
    this.rightUpperArm = new THREE.Group();
    this.rightUpperArm.position.set(0.28, 0.12, 0);
    this.chest.add(this.rightUpperArm);

    const rightBicep = new THREE.Mesh(armGeom, suitMat);
    rightBicep.castShadow = true;
    this.rightUpperArm.add(rightBicep);

    this.rightForearm = new THREE.Mesh(forearmGeom, accentMat);
    this.rightForearm.position.y = -0.28;
    this.rightForearm.castShadow = true;
    this.rightUpperArm.add(this.rightForearm);

    // 7. Left Leg
    this.leftThigh = new THREE.Group();
    this.leftThigh.position.set(-0.14, -0.05, 0);
    this.pelvis.add(this.leftThigh);

    const thighGeom = new THREE.BoxGeometry(0.15, 0.44, 0.15);
    thighGeom.translate(0, -0.2, 0);
    this.geometries.push(thighGeom);
    const leftThighMesh = new THREE.Mesh(thighGeom, suitMat);
    leftThighMesh.castShadow = true;
    this.leftThigh.add(leftThighMesh);

    const shinGeom = new THREE.BoxGeometry(0.13, 0.44, 0.14);
    shinGeom.translate(0, -0.2, 0.02);
    this.geometries.push(shinGeom);
    this.leftShin = new THREE.Mesh(shinGeom, accentMat);
    this.leftShin.position.y = -0.42;
    this.leftShin.castShadow = true;
    this.leftThigh.add(this.leftShin);

    const footGeom = new THREE.BoxGeometry(0.14, 0.08, 0.22);
    footGeom.translate(0, -0.42, 0.06);
    this.geometries.push(footGeom);
    const leftFoot = new THREE.Mesh(footGeom, jointMat);
    leftFoot.castShadow = true;
    this.leftShin.add(leftFoot);

    // 8. Right Leg
    this.rightThigh = new THREE.Group();
    this.rightThigh.position.set(0.14, -0.05, 0);
    this.pelvis.add(this.rightThigh);

    const rightThighMesh = new THREE.Mesh(thighGeom, suitMat);
    rightThighMesh.castShadow = true;
    this.rightThigh.add(rightThighMesh);

    this.rightShin = new THREE.Mesh(shinGeom, accentMat);
    this.rightShin.position.y = -0.42;
    this.rightShin.castShadow = true;
    this.rightThigh.add(this.rightShin);

    const rightFoot = new THREE.Mesh(footGeom, jointMat);
    rightFoot.castShadow = true;
    this.rightShin.add(rightFoot);
  }

  public animate(state: LocomotionState, speed: number, dt: number): void {
    this.animTime += dt;

    // Smooth crouch blend (0 = standing, 1 = crouching)
    const targetCrouch = state === 'crouch' ? 1.0 : 0.0;
    this.currentCrouchBlend = THREE.MathUtils.lerp(this.currentCrouchBlend, targetCrouch, Math.min(1.0, dt * 14));

    // Base Pelvis height
    const standingHeight = 0.95;
    const crouchingHeight = 0.58;
    this.pelvis.position.y = THREE.MathUtils.lerp(standingHeight, crouchingHeight, this.currentCrouchBlend);

    // Crouch spine and leg flex
    const crouchSpineLean = this.currentCrouchBlend * 0.35;
    const crouchLegFlex = this.currentCrouchBlend * 0.55;

    // Reset base rotations
    this.torso.rotation.set(crouchSpineLean, 0, 0);
    this.chest.rotation.set(crouchSpineLean * 0.5, 0, 0);
    this.head.rotation.set(-crouchSpineLean * 0.8, 0, 0);

    if (state === 'jump') {
      // Upward leap: legs slightly tucked, arms raised for balance
      this.leftThigh.rotation.set(0.7, 0, -0.1);
      this.rightThigh.rotation.set(0.4, 0, 0.1);
      this.leftShin.rotation.set(-0.8, 0, 0);
      this.rightShin.rotation.set(-0.5, 0, 0);
      this.leftUpperArm.rotation.set(-0.8, 0, -0.3);
      this.rightUpperArm.rotation.set(-0.8, 0, 0.3);
      return;
    }

    if (state === 'fall') {
      // Downward falling posture
      this.leftThigh.rotation.set(0.3, 0, -0.15);
      this.rightThigh.rotation.set(0.3, 0, 0.15);
      this.leftShin.rotation.set(-0.3, 0, 0);
      this.rightShin.rotation.set(-0.3, 0, 0);
      this.leftUpperArm.rotation.set(-0.4, 0, -0.5);
      this.rightUpperArm.rotation.set(-0.4, 0, 0.5);
      return;
    }

    if (speed > 0.15) {
      // Locomotion (Walk / Sprint / Crouch-Walk)
      const isSprinting = state === 'sprint';
      const strideRate = isSprinting ? 14.0 : state === 'crouch' ? 7.0 : 9.5;
      const cycle = this.animTime * strideRate;

      const legSwingMax = isSprinting ? 0.95 : state === 'crouch' ? 0.45 : 0.65;
      const armSwingMax = isSprinting ? 1.1 : state === 'crouch' ? 0.35 : 0.65;

      const leftLegAngle = Math.sin(cycle) * legSwingMax;
      const rightLegAngle = -Math.sin(cycle) * legSwingMax;

      this.leftThigh.rotation.x = leftLegAngle + crouchLegFlex;
      this.rightThigh.rotation.x = rightLegAngle + crouchLegFlex;

      // Knee bending on back swing
      this.leftShin.rotation.x = Math.sin(cycle) > 0 ? -Math.sin(cycle) * 0.8 : -crouchLegFlex;
      this.rightShin.rotation.x = -Math.sin(cycle) > 0 ? Math.sin(cycle) * 0.8 : -crouchLegFlex;

      // Opposing arm swings
      this.leftUpperArm.rotation.x = -leftLegAngle * (armSwingMax / legSwingMax);
      this.rightUpperArm.rotation.x = -rightLegAngle * (armSwingMax / legSwingMax);

      // Elbow flex
      this.leftForearm.rotation.x = -0.3 - Math.abs(Math.sin(cycle)) * 0.4;
      this.rightForearm.rotation.x = -0.3 - Math.abs(Math.sin(cycle)) * 0.4;

      // Torso lean and bob
      const sprintLean = isSprinting ? 0.28 : 0.08;
      this.torso.rotation.x = crouchSpineLean + sprintLean;
      this.torso.rotation.y = Math.sin(cycle) * 0.08; // Counter twist

      // Vertical bounce
      const bounce = Math.abs(Math.sin(cycle * 2)) * (isSprinting ? 0.07 : 0.035);
      this.pelvis.position.y += bounce;
    } else {
      // Idle Breathing
      const breath = Math.sin(this.animTime * 2.2) * 0.025;
      this.chest.position.y = 0.28 + breath;
      this.leftUpperArm.rotation.set(breath * 2, 0, -0.08);
      this.rightUpperArm.rotation.set(breath * 2, 0, 0.08);
      this.leftForearm.rotation.set(-0.15, 0, 0);
      this.rightForearm.rotation.set(-0.15, 0, 0);

      this.leftThigh.rotation.set(crouchLegFlex, 0, 0);
      this.rightThigh.rotation.set(crouchLegFlex, 0, 0);
      this.leftShin.rotation.set(-crouchLegFlex, 0, 0);
      this.rightShin.rotation.set(-crouchLegFlex, 0, 0);
    }
  }

  public setWireframe(wireframe: boolean): void {
    this.materials.forEach((mat) => {
      (mat as THREE.MeshStandardMaterial).wireframe = wireframe;
    });
  }

  public dispose(): void {
    this.geometries.forEach((g) => g.dispose());
    this.materials.forEach((m) => m.dispose());
  }
}
