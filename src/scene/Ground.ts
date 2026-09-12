import * as THREE from 'three';

export class Ground {
  public mesh: THREE.Mesh;
  private geometry: THREE.PlaneGeometry;
  private material: THREE.MeshStandardMaterial;
  private texture: THREE.Texture;

  constructor(size: number = 160) {
    this.geometry = new THREE.PlaneGeometry(size, size, 32, 32);
    this.geometry.rotateX(-Math.PI / 2);

    // Procedural grid canvas texture for clean high-contrast visual reference
    if (typeof document !== 'undefined') {
      const canvas = document.createElement('canvas');
      canvas.width = 512;
      canvas.height = 512;
      const ctx = canvas.getContext('2d')!;

      // Background slate
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(0, 0, 512, 512);

      // Outer grid lines
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 4;
      ctx.strokeRect(0, 0, 512, 512);

      // Sub-grid lines
      ctx.strokeStyle = '#283548';
      ctx.lineWidth = 1.5;
      for (let i = 64; i < 512; i += 64) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, 512);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(512, i);
        ctx.stroke();
      }

      this.texture = new THREE.CanvasTexture(canvas);
      this.texture.wrapS = THREE.RepeatWrapping;
      this.texture.wrapT = THREE.RepeatWrapping;
      this.texture.repeat.set(size / 4, size / 4);
    } else {
      this.texture = new THREE.DataTexture(new Uint8Array([30, 41, 59, 255]), 1, 1);
    }

    this.material = new THREE.MeshStandardMaterial({
      map: this.texture,
      roughness: 0.85,
      metalness: 0.1,
    });

    this.mesh = new THREE.Mesh(this.geometry, this.material);
    this.mesh.position.set(0, 0, 0);
    this.mesh.receiveShadow = true;
  }

  public setWireframe(wireframe: boolean): void {
    this.material.wireframe = wireframe;
  }

  public dispose(): void {
    this.geometry.dispose();
    this.material.dispose();
    this.texture.dispose();
  }
}
