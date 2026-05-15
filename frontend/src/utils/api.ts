import axios from 'axios'
import { MarketsResponse, CommoditiesResponse, HistoricalData, PredictionResponse, ExplainResponse } from '../types'
import { fetchPrediction, fetchComparison, fetchTopSummary, fetchInsightsData } from './mockApi'
import { COMMODITIES, MARKETS, COMMODITY_BASE_PRICES, MARKET_MULTIPLIERS, XAI_FEATURES } from '../constants'

// Linear Congruential Generator for seeded random numbers
class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  next(): number {
    this.seed = (this.seed * 1664525 + 1013904223) % 4294967296;
    return this.seed / 4294967296;
  }

  nextInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  nextFloat(min: number, max: number): number {
    return this.next() * (max - min) + min;
  }
}

function createSeed(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

function createSeededRandomGenerator(seed: number): SeededRandom {
  return new SeededRandom(seed);
}

const API_BASE = 'http://localhost:8000'
const client = axios.create({ baseURL: API_BASE, timeout: 30_000 })

export async function getMarkets(): Promise<MarketsResponse>{
  try {
    const response = await client.get('/markets');
    return response.data;
  } catch (error) {
    console.warn('API call failed, falling back to mock data:', error);
    // Fallback to mock data
    await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 300));
    return { markets: [...MARKETS] };
  }
}

export async function getCommodities(market: string): Promise<CommoditiesResponse>{
  try {
    const response = await client.get(`/markets/${market}/commodities`);
    return response.data;
  } catch (error) {
    console.warn('API call failed, falling back to mock data:', error);
    // Fallback to mock data
    await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 300));
    return { commodities: [...COMMODITIES] };
  }
}

export async function fetchHistorical(market: string, commodity: string, days=30): Promise<HistoricalData>{
  try {
    // Try to get historical data from API
    const response = await client.get(`/historical-prices/${commodity}`, {
      params: { market, days }
    });
    // Convert API response to expected format
    const data = response.data;
    if (data && data.prices && Array.isArray(data.prices)) {
      const prices = data.prices.map((item: any) => item.price || item);
      const dates = data.prices.map((item: any, index: number) => {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - index));
        return date.toISOString().split('T')[0];
      });
      return { dates, prices };
    }
    throw new Error('Invalid API response format');
  } catch (error) {
    console.warn('API call failed, falling back to mock data:', error);
    // Fallback to mock data
    const seed = createSeed(`${market}-${commodity}-historical`);
    const rng = createSeededRandomGenerator(seed);

    const basePrice = COMMODITY_BASE_PRICES[commodity] || 25;
    const marketMultiplier = MARKET_MULTIPLIERS[market] || 1.0;

    const prices: number[] = [];
    const dates: string[] = [];
    const now = new Date();

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      // Generate price with trend, seasonality, and noise
      const trend = (i / days) * 2; // Slight upward trend
      const seasonality = Math.sin((i / 7) * 2 * Math.PI) * 3; // Weekly seasonality
      const noise = rng.nextFloat(-2, 2);
      const price = (basePrice + trend + seasonality + noise) * marketMultiplier;

      prices.push(Math.max(5, price));
      dates.push(date.toISOString().split('T')[0]);
    }

    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, Math.random() * 800 + 400));

    return { dates, prices };
  }
}

export async function createPrediction(market:string, commodity:string, horizon:number): Promise<PredictionResponse>{
  try {
    const response = await client.post('/predict', {
      market,
      commodity,
      horizon
    });
    const data = response.data;

    // Convert API response to expected format
    return {
      prediction_id: data.prediction_id,
      yhat: data.yhat || [],
      intervals: data.intervals || {},
      base_preds: data.base_preds || {},
      current_market_price: data.current_market_price,
      scraped_price_data: data.scraped_price_data
    };
  } catch (error) {
    console.warn('API call failed, falling back to mock data:', error);
    // Fallback to mock data
    const mockData = await fetchPrediction(commodity, market, horizon);

    // Convert to old format
    const yhat = [...mockData.historical_prices, ...mockData.predicted_prices];
    const intervals = {
      '80%': yhat.map(price => [price * 0.9, price * 1.1] as [number, number]),
      '95%': yhat.map(price => [price * 0.8, price * 1.2] as [number, number])
    };

    return {
      prediction_id: mockData.prediction_id,
      yhat,
      intervals,
      base_preds: { 'ensemble': yhat }
    };
  }
}

export async function getExplain(predictionId: string): Promise<ExplainResponse>{
  try {
    const response = await client.get(`/predictions/${predictionId}/explain`);
    return response.data;
  } catch (error) {
    console.warn('API call failed, falling back to mock data:', error);
    // Fallback to mock data
    const seed = createSeed(`explain-${predictionId}`);
    const rng = createSeededRandomGenerator(seed);

    const global_importance = XAI_FEATURES.map((feature, i) => ({
      feature,
      importance: Math.max(0.1, rng.nextFloat(0.2, 0.8) - i * 0.1)
    }));

    const local = XAI_FEATURES.slice(0, 4).map((feature, i) => ({
      feature,
      contribution: rng.nextFloat(-0.05, 0.05)
    }));

    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, Math.random() * 800 + 400));

    return {
      model_metadata: { source: 'ensemble-model' },
      global_importance,
      local
    };
  }
}

// New mock API functions
export { fetchPrediction, fetchComparison, fetchTopSummary, fetchInsightsData } from './mockApi';

// Wrapper function for fetchComparison with forecast flag
export async function fetchComparisonForecast(commodity: string, isForecast: boolean = false): Promise<any> {
  return fetchComparison(commodity);
}
