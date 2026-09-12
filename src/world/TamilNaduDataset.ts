import { RegionalDefinition, RoadSegment, VegetationRule } from './types';

/**
 * FICTIONALIZED TAMIL NADU GEOGRAPHIC LAYOUT (PLACEHOLDER DATASET)
 *
 * NOTE: The coordinates, elevations, and landmark placements in this file
 * are procedural placeholders designed with geographically sensible relative
 * positioning across the state of Tamil Nadu, India.
 *
 * This dataset is structured according to the `RegionalDefinition` specification
 * so that authoritative, licensed, or open geographic datasets (such as
 * OpenStreetMap, Bhuvan / ISRO DEM, or SRTM data) can directly populate
 * or replace these records in future production stages.
 */
export const TAMIL_NADU_REGIONS: RegionalDefinition[] = [
  {
    id: 'chennai',
    name: 'Chennai Metropolis',
    tamilName: 'சென்னை',
    center: { x: 600, z: -1500 },
    radius: 350,
    baseElevationMeters: 4,
    biome: 'urban',
    description: 'Northeastern coastal capital along the Bay of Bengal, featuring port infrastructure, Marina-style promenade, and urban corridors.',
    landmarks: ['Central Transit Hub', 'Marina Coastal Promenade', 'Harbor Cranes District'],
    placeholderColorHex: 0x94a3b8, // Slate urban
    fogDensity: 0.0008,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'villupuram',
    name: 'Villupuram Transit Junction',
    tamilName: 'விழுப்புரம்',
    center: { x: 200, z: -1100 },
    radius: 280,
    baseElevationMeters: 28,
    biome: 'scrub',
    description: 'Central transport crossroads linking northern coastal corridors with the southern plains and Cauvery basin.',
    landmarks: ['Railway Junction Interchange', 'Highway Cloverleaf', 'Agricultural Market Yard'],
    placeholderColorHex: 0xd97706, // Amber scrub
    fogDensity: 0.0007,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'puducherry',
    name: 'Puducherry-Inspired Coast',
    tamilName: 'புதுச்சேரி',
    center: { x: 520, z: -1000 },
    radius: 260,
    baseElevationMeters: 6,
    biome: 'coastal',
    description: 'Seaside coastal region with pastel colonial facades, oceanfront promenade, and historic lighthouse.',
    landmarks: ['Promenade Beachfront', 'Colonial Heritage Quarter', 'Seaside Lighthouse'],
    placeholderColorHex: 0x38bdf8, // Sky cyan
    fogDensity: 0.001,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'cuddalore',
    name: 'Cuddalore Coastal Port',
    tamilName: 'கடலூர்',
    center: { x: 480, z: -800 },
    radius: 240,
    baseElevationMeters: 8,
    biome: 'coastal',
    description: 'Coastal fishing port and river estuary region south of Puducherry, known for fishing catamarans and beaches.',
    landmarks: ['Fishing Harbor Wharf', 'Silver Beach Dunes', 'Estuary Channel'],
    placeholderColorHex: 0x0284c7, // Ocean blue
    fogDensity: 0.0011,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'salem',
    name: 'Salem & Shevaroy Foothills',
    tamilName: 'சேலம்',
    center: { x: -200, z: -950 },
    radius: 280,
    baseElevationMeters: 75,
    biome: 'scrub',
    description: 'North-central regional hub nestled below the Shevaroy hills, known for steel production and mango orchards.',
    landmarks: ['Steel Industrial Complex', 'Shevaroy Foothills Pass', 'Central Market'],
    placeholderColorHex: 0xb45309, // Rust red-brown
    fogDensity: 0.0008,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'coimbatore',
    name: 'Coimbatore Textile Plateau',
    tamilName: 'கோயம்புத்தூர்',
    center: { x: -600, z: -600 },
    radius: 320,
    baseElevationMeters: 90,
    biome: 'plateau',
    description: 'Western industrial plateau city situated in the rain shadow of the Western Ghats and Nilgiri mountains.',
    landmarks: ['Textile Engineering District', 'Ghats Western Gateway', 'Noyyal Basin'],
    placeholderColorHex: 0x64748b, // Cool industrial slate
    fogDensity: 0.0009,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'ooty',
    name: 'Nilgiris / Ooty-Inspired Mountains',
    tamilName: 'நீலகிரி - ஊட்டி',
    center: { x: -1000, z: -850 },
    radius: 380,
    baseElevationMeters: 190, // Highland elevation
    biome: 'mountain',
    description: 'Highland mountain sanctuary surrounded by misty tea plantations, eucalyptus pine groves, and winding ghat hairpin bends.',
    landmarks: ['Doddabetta Mountain Lookout', 'Stepped Tea Terrace Estate', 'Pine Forest Ridge'],
    placeholderColorHex: 0x15803d, // Deep alpine green
    fogDensity: 0.0035, // Dense mountain mist
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'trichy',
    name: 'Tiruchirappalli (Trichy)',
    tamilName: 'திருச்சிராப்பள்ளி',
    center: { x: 50, z: -500 },
    radius: 290,
    baseElevationMeters: 35,
    biome: 'cultural',
    description: 'Historic city centered around the Kaveri river plains and the dramatic monolithic Rockfort inselberg rising from the plain.',
    landmarks: ['Rockfort Monolithic Inselberg', 'Kaveri River Bridge', 'Chathiram Transit Depot'],
    placeholderColorHex: 0xca8a04, // Golden stone
    fogDensity: 0.0009,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'thanjavur',
    name: 'Thanjavur & Cauvery Delta',
    tamilName: 'தஞ்சாவூர்',
    center: { x: 300, z: -550 },
    radius: 320,
    baseElevationMeters: 22,
    biome: 'delta',
    description: 'The agricultural rice bowl of Tamil Nadu. Lush emerald paddy fields, irrigation waterways, and Great Dravidian Temple architecture.',
    landmarks: ['Great Brihadisvara Gopuram', 'Grand Anicut Canal Network', 'Delta Paddy Terraces'],
    placeholderColorHex: 0x22c55e, // Vibrant emerald paddy
    fogDensity: 0.0012,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'madurai',
    name: 'Madurai Temple City',
    tamilName: 'மதுரை',
    center: { x: -50, z: 0 },
    radius: 350,
    baseElevationMeters: 45,
    biome: 'cultural',
    description: 'Ancient heritage city along the Vaigai river basin, crowned by monumental Meenakshi temple Gopurams and vibrant markets.',
    landmarks: ['Meenakshi Gopuram Gateways', 'Vaigai Riverbed Promenade', 'Goripalayam Heritage Bazaar'],
    placeholderColorHex: 0xeab308, // Heritage saffron gold
    fogDensity: 0.0008,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'tirunelveli',
    name: 'Tirunelveli & Thamirabarani',
    tamilName: 'திருநெல்வேலி',
    center: { x: -150, z: 550 },
    radius: 300,
    baseElevationMeters: 32,
    biome: 'scrub',
    description: 'Southern river basin city surrounded by red sand loam plains (Theri kaadu) and the Thamirabarani perennial river.',
    landmarks: ['Thamirabarani River Steps', 'Nellaiappar Chariot Stand', 'Wind Turbine Windmill Pass'],
    placeholderColorHex: 0xe11d48, // Terra-cotta red soil
    fogDensity: 0.0007,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
  {
    id: 'kanyakumari',
    name: 'Kanyakumari Southern Cape',
    tamilName: 'கன்னியாகுமரி',
    center: { x: -50, z: 1000 },
    radius: 320,
    baseElevationMeters: 10,
    biome: 'cape',
    description: 'The southernmost rocky cape of the Indian subcontinent where the Bay of Bengal, Arabian Sea, and Indian Ocean meet.',
    landmarks: ['Vivekananda Rock Monument', 'Triveni Confluence Sunrise Ghat', 'Southern Cape Highway'],
    placeholderColorHex: 0x06b6d4, // Cyan ocean confluence
    fogDensity: 0.001,
    meta: { dataSource: 'procedural-placeholder', isPlaceholder: true },
  },
];

/**
 * Placeholder Road Corridors connecting regional hubs
 */
export const PLACEHOLDER_ROAD_CORRIDORS: RoadSegment[] = [
  {
    id: 'nh45_grand_southern',
    name: 'NH45 Grand Southern Expressway (Chennai -> Villupuram -> Trichy -> Madurai -> Tirunelveli -> Kanyakumari)',
    points: [
      { x: 600, z: -1500 },
      { x: 400, z: -1300 },
      { x: 200, z: -1100 },
      { x: 100, z: -800 },
      { x: 50, z: -500 },
      { x: 0, z: -250 },
      { x: -50, z: 0 },
      { x: -100, z: 280 },
      { x: -150, z: 550 },
      { x: -100, z: 800 },
      { x: -50, z: 1000 },
    ],
    width: 10,
    hierarchy: 'expressway',
  },
  {
    id: 'western_corridor',
    name: 'Western Highway Corridor (Trichy -> Salem -> Coimbatore -> Nilgiris Ghats)',
    points: [
      { x: 50, z: -500 },
      { x: -100, z: -750 },
      { x: -200, z: -950 },
      { x: -400, z: -750 },
      { x: -600, z: -600 },
      { x: -800, z: -720 },
      { x: -1000, z: -850 },
    ],
    width: 8,
    hierarchy: 'state_highway',
  },
  {
    id: 'east_coast_road',
    name: 'East Coast Scenic Road (Chennai -> Puducherry -> Cuddalore -> Thanjavur)',
    points: [
      { x: 600, z: -1500 },
      { x: 560, z: -1250 },
      { x: 520, z: -1000 },
      { x: 480, z: -800 },
      { x: 380, z: -650 },
      { x: 300, z: -550 },
    ],
    width: 8,
    hierarchy: 'state_highway',
  },
];

/**
 * Placeholder Vegetation Distribution Rules across Biomes
 */
export const VEGETATION_RULES: VegetationRule[] = [
  {
    type: 'palm',
    densityPerChunk: 14,
    minElevation: 0,
    maxElevation: 35,
    allowedBiomes: ['coastal', 'delta', 'cape'],
  },
  {
    type: 'banyan',
    densityPerChunk: 8,
    minElevation: 10,
    maxElevation: 110,
    allowedBiomes: ['cultural', 'scrub', 'urban', 'plateau'],
  },
  {
    type: 'pine',
    densityPerChunk: 18,
    minElevation: 100,
    maxElevation: 300,
    allowedBiomes: ['mountain'],
  },
  {
    type: 'scrub',
    densityPerChunk: 12,
    minElevation: 15,
    maxElevation: 120,
    allowedBiomes: ['scrub', 'plateau'],
  },
];
