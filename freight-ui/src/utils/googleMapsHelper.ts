/**
 * Utility functions for generating Google Maps Directions URLs
 * No API key required - uses the public Google Maps web interface
 */

/**
 * Cleans a location string by removing internal region codes
 * (e.g., "BREMERHAVEN, HB, GERMANY" -> "BREMERHAVEN, GERMANY")
 */
export function cleanLocationString(location: string): string {
  if (!location) return '';
  
  // Split by commas and trim
  const parts = location.split(',').map(s => s.trim());
  
  // Common region codes to filter out (state/province abbreviations)
  const regionCodes = [
    'HB', 'NW', 'BY', 'BW', 'HE', 'RP', 'BB', // German states
    'DROME', 'FRANCE', // Already has country
  ];
  
  // Filter out single/two-letter codes and known region abbreviations
  const filtered = parts.filter(part => {
    // Keep if it's a longer name or if it looks like a country
    if (part.length > 3) return true;
    // Remove if it's a known region code
    if (regionCodes.includes(part.toUpperCase())) return false;
    // Keep otherwise
    return true;
  });
  
  return filtered.join(', ');
}

/**
 * Generates a Google Maps Directions URL for opening in a new tab
 * @param origin - Starting location (e.g., "Le Havre, France")
 * @param destination - Ending location (e.g., "Bremerhaven, Germany")
 * @param travelMode - Optional travel mode: driving (default), walking, bicycling, transit
 * @returns Full Google Maps Directions URL
 */
export function generateGoogleMapsDirectionsUrl(
  origin: string,
  destination: string,
  travelMode: 'driving' | 'walking' | 'bicycling' | 'transit' = 'driving'
): string {
  const cleanOrigin = cleanLocationString(origin);
  const cleanDestination = cleanLocationString(destination);
  
  const baseUrl = 'https://www.google.com/maps/dir/?api=1';
  const params = new URLSearchParams({
    origin: cleanOrigin,
    destination: cleanDestination,
    travelmode: travelMode,
  });
  
  return `${baseUrl}&${params.toString()}`;
}

/**
 * Rough distance estimation between two locations based on city/country names
 * This is a simplified approach that categorizes routes by typical distances
 */
function estimateDistance(origin: string, destination: string): number {
  const origLower = origin.toLowerCase();
  const destLower = destination.toLowerCase();
  
  // Extract country names
  const getCountry = (location: string): string => {
    const lower = location.toLowerCase();
    if (lower.includes('germany')) return 'germany';
    if (lower.includes('france')) return 'france';
    if (lower.includes('netherlands')) return 'netherlands';
    if (lower.includes('belgium')) return 'belgium';
    if (lower.includes('italy')) return 'italy';
    if (lower.includes('austria')) return 'austria';
    if (lower.includes('poland')) return 'poland';
    if (lower.includes('hungary')) return 'hungary';
    return '';
  };
  
  const originCountry = getCountry(origLower);
  const destCountry = getCountry(destLower);
  
  // Same city or very close (within same region)
  if (origLower.includes(destLower.split(',')[0]) || destLower.includes(origLower.split(',')[0])) {
    return 30; // ~30km
  }
  
  // Germany internal routes
  if (originCountry === 'germany' && destCountry === 'germany') {
    // Major port cities to inland destinations
    if ((origLower.includes('hamburg') || origLower.includes('bremerhaven')) && 
        (destLower.includes('muenster') || destLower.includes('dortmund'))) {
      return 200; // ~200km
    }
    if ((origLower.includes('hamburg') || origLower.includes('bremerhaven')) &&
        (destLower.includes('fuerth') || destLower.includes('forchheim'))) {
      return 450; // ~450km
    }
    return 300; // Default Germany internal
  }
  
  // Belgium/Netherlands to Germany
  if ((originCountry === 'belgium' || originCountry === 'netherlands') && destCountry === 'germany') {
    return 350; // ~350km average
  }
  
  // France routes
  if (originCountry === 'france' || destCountry === 'france') {
    if (destCountry === 'germany' || originCountry === 'germany') {
      return 600; // ~600km
    }
  }
  
  // Italy routes
  if (originCountry === 'italy' || destCountry === 'italy') {
    return 900; // ~900km
  }
  
  // Austria routes
  if (originCountry === 'austria' || destCountry === 'austria') {
    return 700; // ~700km
  }
  
  // Poland routes
  if (originCountry === 'poland' || destCountry === 'poland') {
    return 800; // ~800km
  }
  
  // Hungary (very distant)
  if (originCountry === 'hungary' || destCountry === 'hungary') {
    return 1200; // ~1200km
  }
  
  // Default for unknown routes
  return 500;
}

/**
 * Estimates appropriate zoom level based on distance between locations
 * @param origin - Starting location
 * @param destination - Ending location
 * @returns Zoom level (higher = more zoomed in)
 * 
 * Zoom levels based on distance:
 * - 0-70 KM: zoom 10 (most zoomed in - increased by 2)
 * - 71-200 KM: zoom 7 (zoomed in)
 * - 201-600 KM: zoom 6 (normal)
 * - 601-1099 KM: zoom 5 (zoomed out)
 * - 1100+ KM: zoom 4 (most zoomed out)
 */
function estimateZoomLevel(origin: string, destination: string): number {
  const distance = estimateDistance(origin, destination);
  
  if (distance <= 70) {
    return 10; // 0-70 km: zoom in twice more from previous level 8 (6+4)
  } else if (distance <= 200) {
    return 7; // 71-200 km: zoom in once from base (6+1)
  } else if (distance <= 600) {
    return 6; // 201-600 km: normal zoom (base)
  } else if (distance <= 1099) {
    return 5; // 601-1099 km: zoom out once (6-1)
  } else {
    return 4; // 1100+ km: zoom out twice (6-2)
  }
}

/**
 * Generates a Google Maps embed URL for an inline iframe preview (no API key required)
 * Uses the public web interface with output=embed. Automatically adjusts zoom based on
 * estimated distance (same country = closer = more zoom, different countries = farther = less zoom).
 */
export function generateGoogleMapsEmbedUrl(
  origin: string,
  destination: string,
  travelMode: 'driving' | 'walking' | 'bicycling' | 'transit' = 'driving'
): string {
  const cleanOrigin = cleanLocationString(origin);
  const cleanDestination = cleanLocationString(destination);

  // Estimate zoom based on location proximity
  const zoom = estimateZoomLevel(origin, destination);

  // dirflg mapping mirrors Google Maps query params
  const modeToFlag: Record<string, string> = {
    driving: 'd',
    walking: 'w',
    bicycling: 'b',
    transit: 'r',
  };

  const params = new URLSearchParams({
    saddr: cleanOrigin,
    daddr: cleanDestination,
    dirflg: modeToFlag[travelMode] ?? 'd',
    output: 'embed',
    z: String(zoom),
  });

  return `https://www.google.com/maps?${params.toString()}`;
}

/**
 * Simple test function to verify URL generation
 */
export function testGoogleMapsUrl(): void {
  const testCases = [
    {
      origin: 'Le Havre, France',
      destination: 'Bremerhaven, Germany',
      expectedOrigin: 'Le Havre, France',
      expectedDest: 'Bremerhaven, Germany',
    },
    {
      origin: 'BREMERHAVEN, HB, GERMANY',
      destination: 'VALENCE, DROME, FRANCE',
      expectedOrigin: 'BREMERHAVEN, GERMANY',
      expectedDest: 'VALENCE, FRANCE',
    },
    {
      origin: 'MUENSTER, NW, GERMANY',
      destination: 'ROTTERDAM, NETHERLANDS',
      expectedOrigin: 'MUENSTER, GERMANY',
      expectedDest: 'ROTTERDAM, NETHERLANDS',
    },
  ];
  
  console.log('=== Google Maps URL Generation Tests ===\n');
  
  testCases.forEach((test, index) => {
    const url = generateGoogleMapsDirectionsUrl(test.origin, test.destination);
    const cleanOrigin = cleanLocationString(test.origin);
    const cleanDest = cleanLocationString(test.destination);
    
    const pass = cleanOrigin === test.expectedOrigin && cleanDest === test.expectedDest;
    
    console.log(`Test ${index + 1}: ${pass ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Origin: "${test.origin}" → "${cleanOrigin}"`);
    console.log(`  Expected: "${test.expectedOrigin}"`);
    console.log(`  Destination: "${test.destination}" → "${cleanDest}"`);
    console.log(`  Expected: "${test.expectedDest}"`);
    console.log(`  URL: ${url}`);
    console.log('');
  });
}

// Uncomment to run tests in browser console:
// testGoogleMapsUrl();
