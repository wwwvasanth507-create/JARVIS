import * as THREE from 'three';
import { WorldStreamer } from '../../src/streaming/WorldStreamer';
import { TAMIL_NADU_REGIONS } from '../../src/world/TamilNaduDataset';
import { elevationSampler } from '../../src/world/ElevationSampler';
import { chunkCoordKey } from '../../src/world/types';

function runStreamingTests() {
  console.log('🧪 Starting World Streaming & Architecture Automated Tests...\n');

  // 1. Verify Regional Definitions
  console.log('--- Test 1: Regional Definitions Coverage ---');
  const requiredRegions = [
    'Chennai',
    'Cuddalore',
    'Puducherry',
    'Villupuram',
    'Salem',
    'Coimbatore',
    'Madurai',
    'Tiruchirappalli',
    'Thanjavur',
    'Tirunelveli',
    'Kanyakumari',
    'Nilgiris',
  ];

  for (const name of requiredRegions) {
    const found = TAMIL_NADU_REGIONS.find((r) => r.name.toLowerCase().includes(name.toLowerCase()));
    if (!found) {
      throw new Error(`Missing required regional definition: ${name}`);
    }
    console.log(`  ✓ Found Region: ${found.name} (${found.biome}) at (${found.center.x}, ${found.center.z})`);
  }
  console.log(`  Total defined regions: ${TAMIL_NADU_REGIONS.length}\n`);

  // 2. Verify Elevation Sampling & Geographically Sensible Relative Positions
  console.log('--- Test 2: Elevation Sampler & Geography Checks ---');
  const nilgirisElev = elevationSampler.getElevation(-850, -400); // Nilgiris mountain
  const coastElev = elevationSampler.getElevation(650, -700); // Coast
  const rockfortElev = elevationSampler.getElevation(50, -500); // Trichy Rockfort

  console.log(`  Nilgiris elevation (Mountain): ${nilgirisElev.toFixed(1)}m`);
  console.log(`  Coast elevation: ${coastElev.toFixed(1)}m`);
  console.log(`  Trichy Rockfort elevation: ${rockfortElev.toFixed(1)}m`);

  if (nilgirisElev <= coastElev) {
    throw new Error(`Expected Nilgiris elevation (${nilgirisElev}) to be higher than coast (${coastElev})`);
  }
  if (rockfortElev < 60) {
    throw new Error(`Expected Rockfort inselberg to elevate prominently (>60m), got ${rockfortElev}`);
  }
  console.log('  ✓ Elevation profile physically consistent.\n');

  // 3. Test Initial World Streaming & Multi-tier LOD Loading
  console.log('--- Test 3: Coordinate-based Chunk Streaming & LOD Generation ---');
  const scene = new THREE.Scene();
  const streamer = new WorldStreamer(scene, {
    chunkSize: 200,
    lod0Radius: 1, // 3x3 = 9 chunks
    lod1Radius: 2, // 5x5 - 9 = 16 chunks
    lod2Radius: 3, // 7x7 - 25 = 24 chunks -> Total 49 chunks
    maxBuildsPerFrame: 10,
  });

  const playerPos = new THREE.Vector3(0, 0, 0);
  const playerVel = new THREE.Vector3(0, 0, 0);

  // Trigger update
  streamer.update(playerPos, playerVel);

  // Pump the background queue frames until all initial chunks build
  let frames = 0;
  while (streamer.getTelemetry().queueLength > 0 && frames < 50) {
    streamer.update(playerPos, playerVel);
    frames++;
  }

  const telem1 = streamer.getTelemetry();
  console.log(`  Initial loading finished in ${frames} frames.`);
  console.log(`  Active chunks: ${telem1.activeChunksCount} (LOD0: ${telem1.lod0Count}, LOD1: ${telem1.lod1Count}, LOD2: ${telem1.lod2Count})`);
  console.log(`  Colliders registered: ${streamer.allChunkColliders.length}`);

  if (telem1.activeChunksCount !== 29) {
    throw new Error(`Expected 29 chunks for circular radius 3, got ${telem1.activeChunksCount}`);
  }
  if (telem1.lod0Count !== 5) {
    throw new Error(`Expected 5 LOD0 chunks, got ${telem1.lod0Count}`);
  }
  if (telem1.lod1Count !== 8) {
    throw new Error(`Expected 8 LOD1 chunks, got ${telem1.lod1Count}`);
  }
  if (telem1.lod2Count !== 16) {
    throw new Error(`Expected 16 LOD2 chunks, got ${telem1.lod2Count}`);
  }
  if (streamer.allChunkColliders.length === 0) {
    throw new Error('Expected LOD0 chunks to register terrain colliders');
  }
  console.log('  ✓ Initial chunk distribution and LOD hierarchy verified.\n');

  // 4. Test Player Motion & Directional Priority Loading
  console.log('--- Test 4: Directional Priority Loading ---');
  // Move player moving rapidly North-East (+X, +Z)
  playerPos.set(400, 0, 400); // chunk (2, 2)
  playerVel.set(15, 0, 15);
  streamer.update(playerPos, playerVel);

  // Pump queue
  frames = 0;
  while (streamer.getTelemetry().queueLength > 0 && frames < 50) {
    streamer.update(playerPos, playerVel);
    frames++;
  }

  const telem2 = streamer.getTelemetry();
  console.log(`  Moved to chunk (2, 2).`);
  console.log(`  Active chunks: ${telem2.activeChunksCount}, Total Loaded: ${telem2.totalLoaded}, Total Unloaded: ${telem2.totalUnloaded}`);

  // Old distant chunks like (-3, -3) must have been unloaded
  const oldChunkKey = chunkCoordKey(-3, -3);
  if (streamer.activeChunks.has(oldChunkKey)) {
    throw new Error(`Expected distant chunk (-3, -3) to be unloaded!`);
  }
  // New chunk (2, 2) must be LOD0
  const centerChunk = streamer.activeChunks.get(chunkCoordKey(2, 2));
  if (!centerChunk || centerChunk.lodLevel !== 0) {
    throw new Error(`Expected chunk (2, 2) to be active at LOD0!`);
  }
  console.log('  ✓ Distant chunks automatically unloaded, player-centered chunks loaded.\n');

  // 5. Test Repeated Loading and Unloading Under Continuous Movement (Stress Test)
  console.log('--- Test 5: Repeated Loading & Unloading Cycles (Stress Test) ---');
  const waypoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(800, 0, 0),      // cx: 4, cz: 0
    new THREE.Vector3(800, 0, 800),    // cx: 4, cz: 4
    new THREE.Vector3(-600, 0, 600),   // cx: -3, cz: 3
    new THREE.Vector3(-600, 0, -600),  // cx: -3, cz: -3
    new THREE.Vector3(0, 0, 0),        // back to center
  ];

  for (let cycle = 1; cycle <= 3; cycle++) {
    console.log(`  --- Cycle ${cycle} ---`);
    for (const wp of waypoints) {
      playerPos.copy(wp);
      playerVel.set(5, 0, 5);
      streamer.update(playerPos, playerVel);

      // Pump background frames
      for (let f = 0; f < 8; f++) {
        streamer.update(playerPos, playerVel);
      }
    }
  }

  // Drain any remaining queue
  let drainFrames = 0;
  while (streamer.getTelemetry().queueLength > 0 && drainFrames < 50) {
    streamer.update(playerPos, playerVel);
    drainFrames++;
  }

  const stressTelem = streamer.getTelemetry();
  console.log(`  Stress Test Completed.`);
  console.log(`  Total Chunks Loaded: ${stressTelem.totalLoaded}`);
  console.log(`  Total Chunks Unloaded: ${stressTelem.totalUnloaded}`);
  console.log(`  Active Chunks in Memory: ${stressTelem.activeChunksCount}`);
  console.log(`  Scene Children Count: ${scene.children.length}`);

  if (stressTelem.totalLoaded < 100) {
    throw new Error(`Expected > 100 chunks loaded across stress test, got ${stressTelem.totalLoaded}`);
  }
  if (stressTelem.totalUnloaded < 50) {
    throw new Error(`Expected > 50 chunks unloaded across stress test, got ${stressTelem.totalUnloaded}`);
  }
  if (stressTelem.activeChunksCount !== 29) {
    throw new Error(`Active chunks count leaked! Expected 29, got ${stressTelem.activeChunksCount}`);
  }
  console.log('  ✓ Repeated loading/unloading test passed with zero leaks and stable chunk pool.\n');

  // 6. Test Streamer Disposal
  console.log('--- Test 6: Streamer Disposal Clean-up ---');
  streamer.dispose();
  const finalTelem = streamer.getTelemetry();
  if (finalTelem.activeChunksCount !== 0 || scene.children.length !== 0) {
    throw new Error(`Expected 0 active chunks and 0 scene children after dispose, got ${finalTelem.activeChunksCount} and ${scene.children.length}`);
  }
  console.log('  ✓ Streamer disposal cleanly released all chunks and meshes.\n');

  console.log('🎉 ALL STREAMING & WORLD ARCHITECTURE TESTS PASSED SUCCESSFULLY!');
}

runStreamingTests();
