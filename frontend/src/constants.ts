export const COMMODITIES = [
  'Brinjal',
  'Green Chilli',
  'Onion',
  'Potato',
  'Tomato'
] as const;

export const MARKETS = [
  'Bowenpally',
  'Erragadda(Rythu_Bazar)',
  'Gudimalkapur',
  'L_B_Nagar',
  'Mahboob_Manison'
] as const;

export const PREDICTION_HORIZONS = [1, 7, 14, 30] as const;

export const COMMODITY_BASE_PRICES: Record<string, number> = {
  'Brinjal': 25,
  'Green Chilli': 35,
  'Onion': 20,
  'Potato': 18,
  'Tomato': 22
};

export const MARKET_MULTIPLIERS: Record<string, number> = {
  'Bowenpally': 1.0,
  'Erragadda(Rythu_Bazar)': 0.95,
  'Gudimalkapur': 1.05,
  'L_B_Nagar': 0.98,
  'Mahboob_Manison': 1.02
};

export const XAI_FEATURES = [
  'Historical Trend',
  'Seasonality',
  'Market Volatility',
  'Price Momentum',
  'Volume Trends'
] as const;

export type Commodity = typeof COMMODITIES[number];
export type Market = typeof MARKETS[number];
