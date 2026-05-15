export interface MarketsResponse { markets: string[] }
export interface CommoditiesResponse { commodities: string[] }

export interface HistoricalData { dates: string[]; prices: number[] }

export interface PredictionResponse {
  prediction_id: string;
  yhat: (number|null)[];
  intervals: { [key:string]: Array<[number|null,number|null]> };
  base_preds: { [key:string]: (number|null)[] };
  current_market_price?: number | null;
  scraped_price_data?: any;
}

export interface FeatureImportance { feature: string; importance: number }
export interface ExplainResponse { model_metadata?: any; global_importance?: FeatureImportance[]; local?: Array<{feature:string, contribution:number}> }
