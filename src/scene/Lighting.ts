import * as THREE from 'three';
import { settings } from '../core/SettingsManager';

export class Lighting {
  public group: THREE.Group = new THREE.Group();
  public sunLight: THREE.DirectionalLight;
  public ambientLight: THREE.HemisphereLight;

  constructor() {
    // Ambient hemisphere light (sky light + ground bounce)
    this.ambientLight = new THREE.HemisphereLight(0xbae6fd, 0x1e293b, 0.6);
    this.group.add(this.ambientLight);

    // Directional sun light
    this.sunLight = new THREE.DirectionalLight(0xfffbeb, 1.8);
    this.sunLight.position.set(25, 45, 20);
    this.sunLight.castShadow = settings.settings.shadows;

    // Shadow map parameters
    this.sunLight.shadow.mapSize.width = settings.settings.shadowMapSize;
    this.sunLight.shadow.mapSize.height = settings.settings.shadowMapSize;
    this.sunLight.shadow.camera.near = 0.5;
    this.sunLight.shadow.camera.far = 150;
    this.sunLight.shadow.camera.left = -40;
    this.sunLight.shadow.camera.right = 40;
    this.sunLight.shadow.camera.top = 40;
    this.sunLight.shadow.camera.bottom = -40;
    this.sunLight.shadow.bias = -0.0005;

    this.group.add(this.sunLight);
    this.group.add(this.sunLight.target);
  }

  public setShadows(enabled: boolean): void {
    this.sunLight.castShadow = enabled;
  }

  public dispose(): void {
    this.sunLight.dispose();
  }
}
