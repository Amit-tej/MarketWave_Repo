// New interfaces for mock data layer
export interface XAIInsight {
  feature: string;
  importance: number;
  description: string;
}

export interface MockPredictionResponse {
  prediction_id: string;
  historical_prices: number[];
  historical_dates: string[];
  predicted_prices: number[];
  predicted_dates: string[];
  final_price: number;
  price_range: [number, number];
  confidence_interval: [number, number];
  trend: 'Increasing' | 'Stable' | 'Decreasing';
  xai_insights: XAIInsight[];
}

export interface MarketPrice {
  market: string;
  price: number;
  price_difference: number;
}

export interface ComparisonResponse {
  commodity: string;
  markets: MarketPrice[];
  best_market: MarketPrice;
  average_price: number;
}

export interface CommoditySummary {
  commodity: string;
  top_market: string;
  modal_price: number;
  volatility: number;
  tier: 'Top Tier' | 'Mid Tier' | 'Value Tier';
}

export interface TopSummaryResponse {
  commodities: CommoditySummary[];
}

export interface CommodityInsights {
  commodity: string;
  current_price: number;
  volatility: number;
  seasonality: number[];
}

export interface InsightsDataResponse {
  commodities: CommodityInsights[];
  highest_price: CommodityInsights;
  most_stable: CommodityInsights;
  most_volatile: CommodityInsights;
}

export interface ErrorResponse {
  error: string;
  message: string;
}
