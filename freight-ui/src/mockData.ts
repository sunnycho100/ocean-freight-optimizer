import { LaneData } from './types';

export const destinations = [
  'VALENCE, DROME, FRANCE',
  'MUENSTER, NW, GERMANY',
  'ROTTERDAM, NETHERLANDS',
  'ANTWERP, BELGIUM',
  'HAMBURG, HH, GERMANY',
];

export const containerTypes = [
  '20 FT Dry',
  '40 FT Dry',
  '40 FT High Cube Dry',
];

export const mockLaneData: LaneData[] = [
  {
    destination: 'VALENCE, DROME, FRANCE',
    containerType: '20 FT Dry',
    currency: 'EUR',
    routes: [
      { rank: 1, pod: 'LE HAVRE, FRANCE', mode: 'Truck', totalRate: 2480, oceanRate: 1509, inlandRate: 971 },
      { rank: 2, pod: 'FOS-SUR-MER, FRANCE', mode: 'Truck', totalRate: 2831, oceanRate: 2635, inlandRate: 196 },
      { rank: 3, pod: 'ANTWERP, BELGIUM', mode: 'Truck', totalRate: 3245, oceanRate: 1509, inlandRate: 1736 },
      { rank: 4, pod: 'ROTTERDAM, NETHERLANDS', mode: 'Barge/Truck', totalRate: 3412, oceanRate: 1509, inlandRate: 1903 },
      { rank: 5, pod: 'HAMBURG, GERMANY', mode: 'Rail/Truck', totalRate: 4325, oceanRate: 1509, inlandRate: 2816 },
    ],
  },
  {
    destination: 'VALENCE, DROME, FRANCE',
    containerType: '40 FT Dry',
    currency: 'EUR',
    routes: [
      { rank: 1, pod: 'LE HAVRE, FRANCE', mode: 'Truck', totalRate: 3504, oceanRate: 2380, inlandRate: 1124 },
      { rank: 2, pod: 'FOS-SUR-MER, FRANCE', mode: 'Truck', totalRate: 4434, oceanRate: 3825, inlandRate: 609 },
      { rank: 3, pod: 'ANTWERP, BELGIUM', mode: 'Truck', totalRate: 5196, oceanRate: 2380, inlandRate: 2816 },
      { rank: 4, pod: 'ROTTERDAM, NETHERLANDS', mode: 'Barge/Truck', totalRate: 5320, oceanRate: 2380, inlandRate: 2940 },
      { rank: 5, pod: 'HAMBURG, GERMANY', mode: 'Rail/Truck', totalRate: 6180, oceanRate: 2380, inlandRate: 3800 },
    ],
  },
  {
    destination: 'MUENSTER, NW, GERMANY',
    containerType: '20 FT Dry',
    currency: 'EUR',
    routes: [
      { rank: 1, pod: 'ROTTERDAM, NETHERLANDS', mode: 'Barge/Truck', totalRate: 2150, oceanRate: 1509, inlandRate: 641 },
      { rank: 2, pod: 'ANTWERP, BELGIUM', mode: 'Truck', totalRate: 2280, oceanRate: 1509, inlandRate: 771 },
      { rank: 3, pod: 'HAMBURG, GERMANY', mode: 'Rail', totalRate: 2390, oceanRate: 1509, inlandRate: 881 },
      { rank: 4, pod: 'BREMERHAVEN, GERMANY', mode: 'Truck', totalRate: 2510, oceanRate: 1509, inlandRate: 1001 },
      { rank: 5, pod: 'LE HAVRE, FRANCE', mode: 'Truck', totalRate: 3850, oceanRate: 1509, inlandRate: 2341 },
    ],
  },
  {
    destination: 'MUENSTER, NW, GERMANY',
    containerType: '40 FT Dry',
    currency: 'EUR',
    routes: [
      { rank: 1, pod: 'ROTTERDAM, NETHERLANDS', mode: 'Barge/Truck', totalRate: 3280, oceanRate: 2380, inlandRate: 900 },
      { rank: 2, pod: 'ANTWERP, BELGIUM', mode: 'Truck', totalRate: 3450, oceanRate: 2380, inlandRate: 1070 },
      { rank: 3, pod: 'HAMBURG, GERMANY', mode: 'Rail', totalRate: 3590, oceanRate: 2380, inlandRate: 1210 },
      { rank: 4, pod: 'BREMERHAVEN, GERMANY', mode: 'Truck', totalRate: 3780, oceanRate: 2380, inlandRate: 1400 },
      { rank: 5, pod: 'LE HAVRE, FRANCE', mode: 'Truck', totalRate: 5420, oceanRate: 2380, inlandRate: 3040 },
    ],
  },
  {
    destination: 'ROTTERDAM, NETHERLANDS',
    containerType: '20 FT Dry',
    currency: 'EUR',
    routes: [
      { rank: 1, pod: 'ROTTERDAM, NETHERLANDS', mode: 'Direct', totalRate: 1509, oceanRate: 1509, inlandRate: 0 },
      { rank: 2, pod: 'ANTWERP, BELGIUM', mode: 'Barge', totalRate: 1680, oceanRate: 1509, inlandRate: 171 },
      { rank: 3, pod: 'HAMBURG, GERMANY', mode: 'Feeder', totalRate: 1890, oceanRate: 1509, inlandRate: 381 },
    ],
  },
  {
    destination: 'ROTTERDAM, NETHERLANDS',
    containerType: '40 FT Dry',
    currency: 'EUR',
    routes: [
      { rank: 1, pod: 'ROTTERDAM, NETHERLANDS', mode: 'Direct', totalRate: 2380, oceanRate: 2380, inlandRate: 0 },
      { rank: 2, pod: 'ANTWERP, BELGIUM', mode: 'Barge', totalRate: 2620, oceanRate: 2380, inlandRate: 240 },
      { rank: 3, pod: 'HAMBURG, GERMANY', mode: 'Feeder', totalRate: 2950, oceanRate: 2380, inlandRate: 570 },
    ],
  },
];

export function getLaneData(destination: string, containerType: string): LaneData | undefined {
  return mockLaneData.find(
    (lane) => lane.destination === destination && lane.containerType === containerType
  );
}
