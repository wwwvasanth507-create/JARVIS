import * as THREE from 'three';
import { ChunkCoord, WorldBounds } from '../world/types';
import { elevationSampler } from '../world/ElevationSampler';
import { TAMIL_NADU_REGIONS, PLACEHOLDER_ROAD_CORRIDORS, VEGETATION_RULES } from '../world/TamilNaduDataset';

export class WorldChunk {
  public coord: ChunkCoord;
  public size: number;
  public bounds: WorldBounds;
  public lodLevel: number = 0; // 0 = High, 1 = Med, 2 = Proxy
  public group: THREE.Group = new THREE.Group();
  public colliders: THREE.Object3D[] = [];

  // Internal resources for clean disposal
  private terrainMesh: THREE.Mesh | null = null;
  private roadGroup: THREE.Group = new THREE.Group();
  private propGroup: THREE.Group = new THREE.Group();
  private geometries: THREE.BufferGeometry[] = [];
  private materials: THREE.Material[] = [];

  constructor(coord: ChunkCoord, size: number = 200, initialLOD: number = 0) {
    this.coord = coord;
    this.size = size;
    this.lodLevel = initialLOD;

    this.bounds = {
      minX: coord.cx * size,
      maxX: (coord.cx + 1) * size,
      minZ: coord.cz * size,
      maxZ: (coord.cz + 1) * size,
    };

    this.group.add(this.roadGroup);
    this.group.add(this.propGroup);

    this.buildChunk(initialLOD);
  }

  public buildChunk(lod: number): void {
    this.lodLevel = lod;
    this.clearGeometry();

    // 1. Terrain Mesh (Subdivisions determined by LOD)
    const subs = lod === 0 ? 24 : lod === 1 ? 12 : 4;
    const geom = new THREE.PlaneGeometry(this.size, this.size, subs, subs);
    geom.rotateX(-Math.PI / 2);
    this.geometries.push(geom);

    const pos = geom.attributes.position;
    const colors: number[] = [];
    const count = pos.count;

    const centerX = this.bounds.minX + this.size / 2;
    const centerZ = this.bounds.minZ + this.size / 2;
    const region = elevationSampler.getNearestRegion(centerX, centerZ);

    const baseColor = new THREE.Color(region.placeholderColorHex);
    const tempColor = new THREE.Color();

    for (let i = 0; i < count; i++) {
      const lx = pos.getX(i);
      const lz = pos.getZ(i);
      const wx = this.bounds.minX + this.size / 2 + lx;
      const wz = this.bounds.minZ + this.size / 2 + lz;

      const y = elevationSampler.getElevation(wx, wz);
      pos.setY(i, y);

      // Subtle natural tint variation
      const noise = elevationSampler.noise2D(wx * 0.05, wz * 0.05) * 0.08;
      tempColor.copy(baseColor);
      tempColor.r = Math.max(0, Math.min(1, tempColor.r + noise));
      tempColor.g = Math.max(0, Math.min(1, tempColor.g + noise));
      tempColor.b = Math.max(0, Math.min(1, tempColor.b + noise));

      colors.push(tempColor.r, tempColor.g, tempColor.b);
    }

    geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geom.computeVertexNormals();

    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.85,
      metalness: 0.05,
      flatShading: lod === 2, // Proxy mesh flat shaded for crisp stylized look
    });
    this.materials.push(mat);

    this.terrainMesh = new THREE.Mesh(geom, mat);
    this.terrainMesh.position.set(centerX, 0, centerZ);
    this.terrainMesh.receiveShadow = lod <= 1;

    this.group.add(this.terrainMesh);

    // Add terrain mesh as collider for Character & Camera in LOD 0
    if (lod === 0) {
      this.colliders.push(this.terrainMesh);
    }

    // 2. Placeholder Road Segments (LOD 0 & 1)
    if (lod <= 1) {
      this.buildRoads();
    }

    // 3. Placeholder City & Vegetation Data (LOD 0 & 1)
    if (lod <= 1) {
      this.buildFeatures(lod);
    }
  }

  private buildRoads(): void {
    const roadMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.9,
      metalness: 0.1,
    });
    this.materials.push(roadMat);

    PLACEHOLDER_ROAD_CORRIDORS.forEach((corridor) => {
      for (let i = 0; i < corridor.points.length - 1; i++) {
        const p1 = corridor.points[i];
        const p2 = corridor.points[i + 1];

        // Check if road segment intersects chunk bounding box
        if (this.segmentIntersectsBounds(p1, p2)) {
          const v1 = new THREE.Vector3(p1.x, elevationSampler.getElevation(p1.x, p1.z) + 0.15, p1.z);
          const v2 = new THREE.Vector3(p2.x, elevationSampler.getElevation(p2.x, p2.z) + 0.15, p2.z);

          const dir = new THREE.Vector3().subVectors(v2, v1);
          const len = dir.length();
          const mid = new THREE.Vector3().addVectors(v1, v2).multiplyScalar(0.5);

          const roadGeom = new THREE.PlaneGeometry(corridor.width, len);
          roadGeom.rotateX(-Math.PI / 2);
          this.geometries.push(roadGeom);

          const roadMesh = new THREE.Mesh(roadGeom, roadMat);
          roadMesh.position.copy(mid);
          roadMesh.lookAt(v2.x, mid.y, v2.z);
          roadMesh.receiveShadow = true;

          this.roadGroup.add(roadMesh);
        }
      }
    });
  }

  private buildFeatures(lod: number): void {
    const centerX = this.bounds.minX + this.size / 2;
    const centerZ = this.bounds.minZ + this.size / 2;
    const region = elevationSampler.getNearestRegion(centerX, centerZ);

    const distToCityCenter = Math.hypot(centerX - region.center.x, centerZ - region.center.z);

    // 1. Placeholder City Blocks if within regional city radius
    if (distToCityCenter < region.radius * 0.7) {
      const cityMat = new THREE.MeshStandardMaterial({
        color: region.placeholderColorHex,
        roughness: 0.5,
        metalness: 0.2,
      });
      this.materials.push(cityMat);

      const numBuildings = lod === 0 ? 5 : 2;
      for (let b = 0; b < numBuildings; b++) {
        const bx = this.bounds.minX + 35 + ((b * 47) % (this.size - 70));
        const bz = this.bounds.minZ + 35 + ((b * 59) % (this.size - 70));
        const by = elevationSampler.getElevation(bx, bz);

        const bw = 10 + (b % 3) * 4;
        const bh = 8 + (b % 4) * 6;
        const bGeom = new THREE.BoxGeometry(bw, bh, bw);
        this.geometries.push(bGeom);

        const bMesh = new THREE.Mesh(bGeom, cityMat);
        bMesh.position.set(bx, by + bh / 2, bz);
        bMesh.castShadow = lod === 0;
        bMesh.receiveShadow = true;

        this.propGroup.add(bMesh);
        if (lod === 0) {
          this.colliders.push(bMesh);
        }
      }
    }

    // 2. Placeholder Vegetation based on regional biome rules
    const treeMat = new THREE.MeshStandardMaterial({
      color: region.biome === 'mountain' ? 0x14532d : 0x15803d,
      roughness: 0.8,
    });
    this.materials.push(treeMat);

    const numTrees = lod === 0 ? 8 : 3;
    for (let t = 0; t < numTrees; t++) {
      const tx = this.bounds.minX + 25 + ((t * 61) % (this.size - 50));
      const tz = this.bounds.minZ + 25 + ((t * 73) % (this.size - 50));
      const ty = elevationSampler.getElevation(tx, tz);

      if (ty < 1.0) continue; // Don't spawn in water

      const treeGeom = new THREE.ConeGeometry(2.0, 7.0, 5);
      this.geometries.push(treeGeom);

      const treeMesh = new THREE.Mesh(treeGeom, treeMat);
      treeMesh.position.set(tx, ty + 3.5, tz);
      treeMesh.castShadow = lod === 0;

      this.propGroup.add(treeMesh);
    }
  }

  private segmentIntersectsBounds(p1: { x: number; z: number }, p2: { x: number; z: number }): boolean {
    const minX = Math.min(p1.x, p2.x);
    const maxX = Math.max(p1.x, p2.x);
    const minZ = Math.min(p1.z, p2.z);
    const maxZ = Math.max(p1.z, p2.z);

    return (
      maxX >= this.bounds.minX &&
      minX <= this.bounds.maxX &&
      maxZ >= this.bounds.minZ &&
      minZ <= this.bounds.maxZ
    );
  }

  private clearGeometry(): void {
    if (this.terrainMesh) {
      this.group.remove(this.terrainMesh);
      this.terrainMesh = null;
    }

    while (this.roadGroup.children.length > 0) {
      this.roadGroup.remove(this.roadGroup.children[0]);
    }

    while (this.propGroup.children.length > 0) {
      this.propGroup.remove(this.propGroup.children[0]);
    }

    this.colliders.length = 0;

    this.geometries.forEach((g) => g.dispose());
    this.geometries.length = 0;

    this.materials.forEach((m) => m.dispose());
    this.materials.length = 0;
  }

  public dispose(): void {
    this.clearGeometry();
    if (this.group.parent) {
      this.group.parent.remove(this.group);
    }
  }
}
