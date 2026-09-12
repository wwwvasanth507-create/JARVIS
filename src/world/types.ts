import * as THREE from 'three';

/**
 * Coordinate-based chunk grid identifier
 */
export interface ChunkCoord {
  cx: number;
  cz: number;
}

export function chunkCoordKey(cx: number, cz: number): string {
  return `${cx},${cz}`;
}

export function parseChunkCoordKey(key: string): ChunkCoord {
  const [cx, cz] = key.split(',').map(Number);
  return { cx, cz };
}

/**
 * Geographic bounding box in world space (meters)
 */
export interface WorldBounds {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
}

/**
 * Interface for terrain elevation sampling.
 * Designed so that procedural noise, GeoTIFF DEMs, or raster heightmaps
 * can implement this same interface interchangeably.
 */
export interface ElevationProvider {
  getElevation(x: number, z: number): number;
  getNormal(x: number, z: number): THREE.Vector3;
}

/**
 * Regional data specification for Tamil Nadu open-world partition.
 * Data structures are designed so real-world GIS/GeoJSON datasets
 * (e.g. OpenStreetMap boundaries, Survey of India DEMs) can replace placeholders.
 */
export type BiomeCategory =
  | 'coastal'
  | 'delta'
  | 'mountain'
  | 'plateau'
  | 'urban'
  | 'cultural'
  | 'scrub'
  | 'cape';

export interface RegionalDefinition {
  id: string;
  name: string;
  tamilName: string;
  center: { x: number; z: number };
  radius: number;
  baseElevationMeters: number;
  biome: BiomeCategory;
  description: string;
  landmarks: string[];
  placeholderColorHex: number;
  fogDensity: number;
  // Metadata for future dataset linkage (e.g. GeoJSON feature properties)
  meta?: {
    osmRelationId?: number;
    dataSource?: string;
    isPlaceholder: boolean;
  };
}

/**
 * Placeholder road network segment
 */
export interface RoadSegment {
  id: string;
  name: string;
  points: { x: number; z: number }[];
  width: number;
  hierarchy: 'expressway' | 'state_highway' | 'rural_road';
}

/**
 * Placeholder vegetation / prop distribution rule
 */
export interface VegetationRule {
  type: 'palm' | 'banyan' | 'pine' | 'scrub';
  densityPerChunk: number;
  minElevation: number;
  maxElevation: number;
  allowedBiomes: BiomeCategory[];
}
