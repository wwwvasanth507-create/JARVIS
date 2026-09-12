import * as THREE from 'three';

export class GymEnvironment {
  public group: THREE.Group = new THREE.Group();
  public colliders: THREE.Object3D[] = [];

  private geometries: THREE.BufferGeometry[] = [];
  private materials: THREE.Material[] = [];

  constructor() {
    this.buildGym();
  }

  private buildGym(): void {
    // Shared PBR Materials
    const concreteMat = new THREE.MeshStandardMaterial({
      color: 0x334155, // Slate concrete
      roughness: 0.8,
      metalness: 0.1,
    });
    const accentMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7, // Cyan trim
      roughness: 0.4,
      metalness: 0.3,
    });
    const woodMat = new THREE.MeshStandardMaterial({
      color: 0x78350f, // Dark amber
      roughness: 0.7,
      metalness: 0.1,
    });
    const warnMat = new THREE.MeshStandardMaterial({
      color: 0xd97706, // Warning amber
      roughness: 0.6,
      metalness: 0.2,
    });
    const dangerMat = new THREE.MeshStandardMaterial({
      color: 0xef4444, // Red for steep slide
      roughness: 0.5,
      metalness: 0.2,
    });

    this.materials.push(concreteMat, accentMat, woodMat, warnMat, dangerMat);

    // ==========================================
    // 1. SLOPES & RAMPS SECTION (X: -18 to -6, Z: -15)
    // ==========================================
    const slopeAngles = [15, 30, 45, 60];
    const rampWidth = 3.2;
    const rampLength = 9.0;

    slopeAngles.forEach((angleDeg, idx) => {
      const angleRad = (angleDeg * Math.PI) / 180;
      const rx = -18 + idx * 4.2;
      const rz = -12;

      const rampGeom = new THREE.BoxGeometry(rampWidth, 0.3, rampLength);
      this.geometries.push(rampGeom);

      const mat = angleDeg === 60 ? dangerMat : angleDeg === 45 ? warnMat : concreteMat;
      const ramp = new THREE.Mesh(rampGeom, mat);

      // Rotate ramp along pitch
      ramp.rotation.x = -angleRad;
      // Position center of ramp so bottom touches ground at y = 0
      const heightRise = Math.sin(angleRad) * rampLength;
      ramp.position.set(rx, heightRise / 2, rz - (Math.cos(angleRad) * rampLength) / 2);
      ramp.castShadow = true;
      ramp.receiveShadow = true;

      this.group.add(ramp);
      this.colliders.push(ramp);

      // Top resting platform
      const platGeom = new THREE.BoxGeometry(rampWidth, 0.3, 3.0);
      this.geometries.push(platGeom);
      const plat = new THREE.Mesh(platGeom, accentMat);
      plat.position.set(rx, heightRise, rz - Math.cos(angleRad) * rampLength - 1.5);
      plat.castShadow = true;
      plat.receiveShadow = true;
      this.group.add(plat);
      this.colliders.push(plat);
    });

    // ==========================================
    // 2. STAIRCASE SECTION (X: 6 to 16, Z: -12)
    // ==========================================
    // Flight A: Standard stairs (0.18m risers, 0.35m treads, 12 steps)
    const numStepsA = 12;
    const riserA = 0.18;
    const treadA = 0.38;
    const stairWidth = 3.5;

    for (let s = 0; s < numStepsA; s++) {
      const stepGeom = new THREE.BoxGeometry(stairWidth, riserA, treadA);
      this.geometries.push(stepGeom);
      const step = new THREE.Mesh(stepGeom, concreteMat);
      step.position.set(8, s * riserA + riserA / 2, -5 - s * treadA);
      step.castShadow = true;
      step.receiveShadow = true;
      this.group.add(step);
      this.colliders.push(step);
    }

    // Top Platform for Flight A
    const topPlatAGeom = new THREE.BoxGeometry(stairWidth, 0.3, 4.0);
    this.geometries.push(topPlatAGeom);
    const topPlatA = new THREE.Mesh(topPlatAGeom, accentMat);
    topPlatA.position.set(8, numStepsA * riserA, -5 - numStepsA * treadA - 2.0);
    topPlatA.castShadow = true;
    topPlatA.receiveShadow = true;
    this.group.add(topPlatA);
    this.colliders.push(topPlatA);

    // Flight B: Steep stairs (0.28m risers - near maxStepHeight, 8 steps)
    const numStepsB = 8;
    const riserB = 0.28;
    const treadB = 0.40;

    for (let s = 0; s < numStepsB; s++) {
      const stepGeom = new THREE.BoxGeometry(stairWidth, riserB, treadB);
      this.geometries.push(stepGeom);
      const step = new THREE.Mesh(stepGeom, warnMat);
      step.position.set(13, s * riserB + riserB / 2, -5 - s * treadB);
      step.castShadow = true;
      step.receiveShadow = true;
      this.group.add(step);
      this.colliders.push(step);
    }

    // ==========================================
    // 3. PLATFORMS & JUMP TOWERS (X: -16 to -6, Z: 10)
    // ==========================================
    const platformHeights = [1.2, 2.4, 3.8];
    platformHeights.forEach((h, idx) => {
      const pGeom = new THREE.BoxGeometry(3.6, h, 3.6);
      this.geometries.push(pGeom);
      const pMesh = new THREE.Mesh(pGeom, concreteMat);
      pMesh.position.set(-15 + idx * 5.0, h / 2, 10);
      pMesh.castShadow = true;
      pMesh.receiveShadow = true;
      this.group.add(pMesh);
      this.colliders.push(pMesh);
    });

    // ==========================================
    // 4. CROUCH TUNNEL (X: 4 to 12, Z: 12)
    // Clearance: 1.35m (Standing: 1.8m cannot enter; Crouch: 1.15m enters cleanly!)
    // ==========================================
    const tunnelLength = 10.0;
    const tunnelWidth = 3.6;
    const tunnelClearance = 1.35;
    const wallThick = 0.4;
    const roofThick = 0.3;

    // Left Wall
    const lWallGeom = new THREE.BoxGeometry(wallThick, tunnelClearance + roofThick, tunnelLength);
    this.geometries.push(lWallGeom);
    const lWall = new THREE.Mesh(lWallGeom, concreteMat);
    lWall.position.set(6 - tunnelWidth / 2, (tunnelClearance + roofThick) / 2, 12);
    lWall.castShadow = true;
    this.group.add(lWall);
    this.colliders.push(lWall);

    // Right Wall
    const rWall = new THREE.Mesh(lWallGeom, concreteMat);
    rWall.position.set(6 + tunnelWidth / 2, (tunnelClearance + roofThick) / 2, 12);
    rWall.castShadow = true;
    this.group.add(rWall);
    this.colliders.push(rWall);

    // Roof (Ceiling obstacle)
    const roofGeom = new THREE.BoxGeometry(tunnelWidth + wallThick * 2, roofThick, tunnelLength);
    this.geometries.push(roofGeom);
    const roof = new THREE.Mesh(roofGeom, accentMat);
    roof.position.set(6, tunnelClearance + roofThick / 2, 12);
    roof.castShadow = true;
    this.group.add(roof);
    this.colliders.push(roof);

    // ==========================================
    // 5. CAMERA COLLISION WALLS & PILLARS (Z: 22 to 26)
    // ==========================================
    // Tall boundary wall to test camera collision avoidance
    const wallGeom = new THREE.BoxGeometry(32.0, 7.0, 1.2);
    this.geometries.push(wallGeom);
    const backWall = new THREE.Mesh(wallGeom, concreteMat);
    backWall.position.set(0, 3.5, 24);
    backWall.castShadow = true;
    backWall.receiveShadow = true;
    this.group.add(backWall);
    this.colliders.push(backWall);

    // Thick concrete pillars
    const pillarGeom = new THREE.CylinderGeometry(1.2, 1.2, 7.0, 16);
    this.geometries.push(pillarGeom);
    [-8, 0, 8].forEach((px) => {
      const pillar = new THREE.Mesh(pillarGeom, accentMat);
      pillar.position.set(px, 3.5, 18);
      pillar.castShadow = true;
      pillar.receiveShadow = true;
      this.group.add(pillar);
      this.colliders.push(pillar);
    });
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
