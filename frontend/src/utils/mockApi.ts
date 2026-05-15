import {
  MockPredictionResponse,
  ComparisonResponse,
  TopSummaryResponse,
  InsightsDataResponse,
  XAIInsight,
  CommoditySummary,
  CommodityInsights,
  MarketPrice
} from '../types_new'
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

// Mock API functions
export async function fetchPrediction(commodity: string, market: string, horizon: number): Promise<MockPredictionResponse> {
  const seed = createSeed(`${commodity}-${market}-${horizon}`);
  const rng = createSeededRandomGenerator(seed);

  // Generate historical data (30 days)
  const historicalPrices: number[] = [];
  const historicalDates: string[] = [];
  const basePrice = COMMODITY_BASE_PRICES[commodity] || 25;
  const marketMultiplier = MARKET_MULTIPLIERS[market] || 1.0;

  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);

    const trend = (i / 30) * 2;
    const seasonality = Math.sin((i / 7) * 2 * Math.PI) * 3;
    const noise = rng.nextFloat(-2, 2);
    const price = (basePrice + trend + seasonality + noise) * marketMultiplier;

    historicalPrices.push(Math.max(5, price));
    historicalDates.push(date.toISOString().split('T')[0]);
  }

  // Generate future predictions
  const predictedPrices: number[] = [];
  const predictedDates: string[] = [];
  let currentPrice = historicalPrices[historicalPrices.length - 1];

  // Determine trend based on recent historical data
  const recentPrices = historicalPrices.slice(-7);
  const trend = recentPrices[recentPrices.length - 1] - recentPrices[0] > 0 ? 'Increasing' :
                recentPrices[recentPrices.length - 1] - recentPrices[0] < -1 ? 'Decreasing' : 'Stable';

  for (let i = 1; i <= horizon; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() + i);

    // Continue the trend with some noise
    const trendMultiplier = trend === 'Increasing' ? 1.02 : trend === 'Decreasing' ? 0.98 : 1.0;
    const noise = rng.nextFloat(-1, 1);
    currentPrice = currentPrice * trendMultiplier + noise;

    predictedPrices.push(Math.max(5, currentPrice));
    predictedDates.push(date.toISOString().split('T')[0]);
  }

  const finalPrice = predictedPrices[predictedPrices.length - 1];
  const priceRange: [number, number] = [
    Math.min(...predictedPrices) * 0.95,
    Math.max(...predictedPrices) * 1.05
  ];
  const confidenceInterval: [number, number] = [
    finalPrice * 0.9,
    finalPrice * 1.1
  ];

  // Generate XAI insights
  const xaiInsights: XAIInsight[] = XAI_FEATURES.map((feature, index) => ({
    feature,
    importance: Math.max(0.1, rng.nextFloat(0.2, 0.8) - index * 0.1),
    description: `${feature} has ${rng.nextFloat(0.3, 0.9) > 0.5 ? 'significant' : 'moderate'} influence on price prediction.`
  })).sort((a, b) => b.importance - a.importance);

  // Simulate network latency and occasional errors
  await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 800));

  // Occasional error simulation
  if (rng.next() < 0.05) {
    throw new Error('Prediction model is currently offline.');
  }

  return {
    prediction_id: `pred_${Date.now()}_${rng.nextInt(1000, 9999)}`,
    historical_prices: historicalPrices,
    historical_dates: historicalDates,
    predicted_prices: predictedPrices,
    predicted_dates: predictedDates,
    final_price: finalPrice,
    price_range: priceRange,
    confidence_interval: confidenceInterval,
    trend: trend as 'Increasing' | 'Stable' | 'Decreasing',
    xai_insights: xaiInsights
  };
}

export async function fetchComparison(commodity: string, isForecast: boolean = false): Promise<ComparisonResponse> {
  const seed = createSeed(`comparison-${commodity}${isForecast ? '-forecast' : ''}`);
  const rng = createSeededRandomGenerator(seed);

  const basePrice = COMMODITY_BASE_PRICES[commodity] || 25;
  const markets: MarketPrice[] = MARKETS.map(market => {
    let price: number;

    if (isForecast) {
      // Generate forecast prices for the market
      const marketSeed = createSeed(`${commodity}-${market}-forecast`);
      const marketRng = createSeededRandomGenerator(marketSeed);
      const marketMultiplier = MARKET_MULTIPLIERS[market] || 1.0;
      const horizon = 7; // Default forecast horizon
      const predictedPrices: number[] = [];
      let currentPrice = basePrice * marketMultiplier;

      for (let i = 1; i <= horizon; i++) {
        const trendMultiplier = 1.02; // Assume slight upward trend
        const noise = marketRng.nextFloat(-1, 1);
        currentPrice = currentPrice * trendMultiplier + noise;
        predictedPrices.push(Math.max(5, currentPrice));
      }

      const averagePrice = predictedPrices.reduce((sum, p) => sum + p, 0) / predictedPrices.length;
      price = Math.round(averagePrice * 100) / 100;
    } else {
      const multiplier = MARKET_MULTIPLIERS[market] || 1.0;
      const variation = rng.nextFloat(-0.1, 0.1);
      price = (basePrice * multiplier * (1 + variation));
      price = Math.round(price * 100) / 100;
    }

    return {
      market,
      price,
      price_difference: 0 // Will calculate after getting all prices
    };
  });

  // Calculate average and price differences
  const averagePrice = markets.reduce((sum, m) => sum + m.price, 0) / markets.length;
  markets.forEach(m => {
    m.price_difference = Math.round((m.price - averagePrice) * 100) / 100;
  });

  const bestMarket = markets.reduce((best, current) =>
    current.price > best.price ? current : best
  );

  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 600));

  return {
    commodity,
    markets,
    best_market: bestMarket,
    average_price: Math.round(averagePrice * 100) / 100
  };
}

export async function fetchTopSummary(): Promise<TopSummaryResponse> {
  const seed = createSeed('top-summary');
  const rng = createSeededRandomGenerator(seed);

  const commodities: CommoditySummary[] = COMMODITIES.map(commodity => {
    const basePrice = COMMODITY_BASE_PRICES[commodity] || 25;

    // Find top market for this commodity
    const marketPrices = MARKETS.map(market => ({
      market,
      price: basePrice * (MARKET_MULTIPLIERS[market] || 1.0) * rng.nextFloat(0.9, 1.1)
    }));

    const topMarket = marketPrices.reduce((top, current) =>
      current.price > top.price ? current : top
    );

    const volatility = rng.nextFloat(5, 25);
    const tier = volatility < 10 ? 'Top Tier' : volatility < 20 ? 'Mid Tier' : 'Value Tier';

    return {
      commodity,
      top_market: topMarket.market,
      modal_price: Math.round(topMarket.price * 100) / 100,
      volatility: Math.round(volatility * 100) / 100,
      tier: tier as 'Top Tier' | 'Mid Tier' | 'Value Tier'
    };
  });

  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));

  return { commodities };
}

export async function fetchInsightsData(): Promise<InsightsDataResponse> {
  const seed = createSeed('insights-data');
  const rng = createSeededRandomGenerator(seed);

  const commodities: CommodityInsights[] = COMMODITIES.map(commodity => {
    const basePrice = COMMODITY_BASE_PRICES[commodity] || 25;
    const currentPrice = basePrice * rng.nextFloat(0.8, 1.2);
    const volatility = rng.nextFloat(5, 30);

    // Generate 12-month seasonality using sine wave
    const seasonality: number[] = [];
    for (let i = 0; i < 12; i++) {
      const seasonalValue = Math.sin((i / 12) * 2 * Math.PI) * 10 + rng.nextFloat(-2, 2);
      seasonality.push(Math.round((basePrice + seasonalValue) * 100) / 100);
    }

    return {
      commodity,
      current_price: Math.round(currentPrice * 100) / 100,
      volatility: Math.round(volatility * 100) / 100,
      seasonality
    };
  });

  const highestPrice = commodities.reduce((max, current) =>
    current.current_price > max.current_price ? current : max
  );

  const mostStable = commodities.reduce((min, current) =>
    current.volatility < min.volatility ? current : min
  );

  const mostVolatile = commodities.reduce((max, current) =>
    current.volatility > max.volatility ? current : max
  );

  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 700));

  return {
    commodities,
    highest_price: highestPrice,
    most_stable: mostStable,
    most_volatile: mostVolatile
  };
}
