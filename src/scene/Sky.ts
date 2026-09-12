import * as THREE from 'three';

export class Sky {
  public mesh: THREE.Mesh;
  private geometry: THREE.SphereGeometry;
  private material: THREE.MeshBasicMaterial;

  constructor() {
    this.geometry = new THREE.SphereGeometry(600, 32, 24);

    const positions = this.geometry.attributes.position;
    const colors: number[] = [];
    const count = positions.count;

    const topColor = new THREE.Color(0x0f172a);    // Deep twilight indigo
    const horizonColor = new THREE.Color(0x38bdf8); // Bright horizon cyan
    const groundColor = new THREE.Color(0x1e293b);  // Subtle lower hemisphere
    const tempColor = new THREE.Color();

    for (let i = 0; i < count; i++) {
      const y = positions.getY(i) / 600; // Normalized -1 to +1

      if (y >= 0) {
        // Upper hemisphere: blend from horizon to zenith
        const t = Math.pow(y, 0.7);
        tempColor.copy(horizonColor).lerp(topColor, t);
      } else {
        // Lower hemisphere: blend from horizon to ground
        const t = Math.min(1.0, -y * 2.0);
        tempColor.copy(horizonColor).lerp(groundColor, t);
      }

      colors.push(tempColor.r, tempColor.g, tempColor.b);
    }

    this.geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    this.material = new THREE.MeshBasicMaterial({
      vertexColors: true,
      side: THREE.BackSide,
      depthWrite: false,
    });

    this.mesh = new THREE.Mesh(this.geometry, this.material);
  }

  public dispose(): void {
    this.geometry.dispose();
    this.material.dispose();
  }
}
