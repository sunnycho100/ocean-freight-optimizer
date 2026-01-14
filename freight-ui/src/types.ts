export interface Route {
  rank: number;
  pod: string;
  mode: string;
  remarks?: string;
  totalRate: number;
  oceanRate?: number;
  inlandRate?: number;
}

export interface LaneData {
  destination: string;
  containerType: string;
  currency: string;
  routes: Route[];
}

export interface FilterState {
  destination: string;
  containerType: string;
}

// HAPAG-LLOYD Types
export type ShippingProvider = 'ONE' | 'HAPAG';

export interface HapagSubOption {
  description: string;
  value20: string;
  value40: string;
  value40HC: string;
}

export interface HapagChargeItem {
  description: string;
  curr: string;
  value20STD: string;
  value40STD: string;
  value40HC: string;
  subOptions?: HapagSubOption[];  // For items with empty curr (like Destination Landfreight)
}

export interface HapagRoute {
  from: string;
  to: string;
  via: string;
  oceanFreight?: HapagChargeItem;
  destinationLandfreight?: HapagChargeItem;
  otherCharges: HapagChargeItem[];
  availableContainers: {
    '20STD': boolean;
    '40STD': boolean;
    '40HC': boolean;
  };
}

export interface HapagLaneData {
  destination: string;
  route: HapagRoute;
}
