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
