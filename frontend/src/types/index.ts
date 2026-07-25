export type AcState = {
  power: 'ON' | 'OFF';
  temperatureC: number | null;
  fanSpeed: 'LOW' | 'MEDIUM' | 'HIGH';
};

export type Detection = {
  label: string;
  confidence: number;
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
};

export type LiveMetrics = {
  timestamp: string;
  occupancyCount: number;
  occupancyBand: 'LOW' | 'MEDIUM' | 'HIGH';
  activity: string;
  acState: AcState;
  confidence: number;
  detections: Detection[];
};

export type HistoryResponse = {
  occupancyHistory: { timestamp: string; occupancyCount: number }[];
  temperatureHistory: { timestamp: string; temperatureC: number }[];
};
