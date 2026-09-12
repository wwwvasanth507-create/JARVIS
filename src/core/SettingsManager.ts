export type QualityPreset = 'low' | 'medium' | 'high' | 'ultra';

export interface GraphicsSettings {
  preset: QualityPreset;
  shadows: boolean;
  shadowMapSize: number;
  maxPixelRatio: number;
  wireframe: boolean;
  fov: number;
}

export class SettingsManager {
  private static instance: SettingsManager;
  public settings: GraphicsSettings;
  private changeListeners: Set<(settings: GraphicsSettings) => void> = new Set();

  private constructor() {
    this.settings = this.getPresetSettings('high');
  }

  public static getInstance(): SettingsManager {
    if (!SettingsManager.instance) {
      SettingsManager.instance = new SettingsManager();
    }
    return SettingsManager.instance;
  }

  public getPresetSettings(preset: QualityPreset): GraphicsSettings {
    switch (preset) {
      case 'low':
        return {
          preset: 'low',
          shadows: false,
          shadowMapSize: 512,
          maxPixelRatio: 1.0,
          wireframe: false,
          fov: 65,
        };
      case 'medium':
        return {
          preset: 'medium',
          shadows: true,
          shadowMapSize: 1024,
          maxPixelRatio: 1.25,
          wireframe: false,
          fov: 65,
        };
      case 'high':
        return {
          preset: 'high',
          shadows: true,
          shadowMapSize: 2048,
          maxPixelRatio: 1.5,
          wireframe: false,
          fov: 65,
        };
      case 'ultra':
        return {
          preset: 'ultra',
          shadows: true,
          shadowMapSize: 4096,
          maxPixelRatio: 2.0,
          wireframe: false,
          fov: 65,
        };
    }
  }

  public setPreset(preset: QualityPreset): void {
    const newSettings = this.getPresetSettings(preset);
    this.settings = newSettings;
    this.notify();
  }

  public setShadows(enabled: boolean): void {
    this.settings.shadows = enabled;
    this.notify();
  }

  public setWireframe(enabled: boolean): void {
    this.settings.wireframe = enabled;
    this.notify();
  }

  public onChange(listener: (settings: GraphicsSettings) => void): () => void {
    this.changeListeners.add(listener);
    return () => this.changeListeners.delete(listener);
  }

  private notify(): void {
    this.changeListeners.forEach((fn) => fn(this.settings));
  }
}

export const settings = SettingsManager.getInstance();
