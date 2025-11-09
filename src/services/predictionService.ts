import * as tf from '@tensorflow/tfjs';
import { linearRegression, mean, standardDeviation } from 'simple-statistics';
import type { StockHistoricalData, StockPrediction, TechnicalIndicator } from '../types/stock';

/**
 * AI Prediction Service
 * 
 * Provides:
 * - Price predictions using ML models
 * - Technical indicators (RSI, MACD, Moving Averages)
 * - Trend analysis
 */

export class PredictionService {
  private static instance: PredictionService;
  private model: tf.LayersModel | null = null;

  private constructor() {
    this.initializeModel();
  }

  static getInstance(): PredictionService {
    if (!PredictionService.instance) {
      PredictionService.instance = new PredictionService();
    }
    return PredictionService.instance;
  }

  /**
   * Initialize a simple LSTM-like model for price prediction
   */
  private async initializeModel(): Promise<void> {
    try {
      // Simple sequential model for time series prediction
      this.model = tf.sequential({
        layers: [
          tf.layers.dense({ inputShape: [10], units: 32, activation: 'relu' }),
          tf.layers.dropout({ rate: 0.2 }),
          tf.layers.dense({ units: 16, activation: 'relu' }),
          tf.layers.dense({ units: 1 }),
        ],
      });

      this.model.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });
    } catch (error) {
      console.error('Error initializing model:', error);
    }
  }

  /**
   * Calculate technical indicators
   */
  calculateTechnicalIndicators(data: StockHistoricalData[]): TechnicalIndicator[] {
    if (data.length < 14) {
      return [];
    }

    const closes = data.map(d => d.close).reverse(); // Oldest first
    const indicators: TechnicalIndicator[] = [];

    // RSI (Relative Strength Index)
    const rsi = this.calculateRSI(closes);
    indicators.push({
      name: 'RSI (14)',
      value: rsi,
      signal: rsi > 70 ? 'sell' : rsi < 30 ? 'buy' : 'hold',
      description: rsi > 70 
        ? 'Overbought - Potential sell signal'
        : rsi < 30 
        ? 'Oversold - Potential buy signal'
        : 'Neutral - No strong signal',
    });

    // Moving Averages
    const sma20 = this.calculateSMA(closes, 20);
    const sma50 = this.calculateSMA(closes, 50);
    const currentPrice = closes[closes.length - 1];

    if (sma20 && sma50) {
      indicators.push({
        name: 'SMA 20/50',
        value: sma20 - sma50,
        signal: sma20 > sma50 && currentPrice > sma20 ? 'buy' : sma20 < sma50 && currentPrice < sma20 ? 'sell' : 'hold',
        description: sma20 > sma50 
          ? 'Bullish crossover - Uptrend'
          : 'Bearish crossover - Downtrend',
      });
    }

    // MACD
    const macd = this.calculateMACD(closes);
    if (macd) {
      indicators.push({
        name: 'MACD',
        value: macd.value,
        signal: macd.signal > 0 ? 'buy' : 'sell',
        description: macd.signal > 0 ? 'Bullish momentum' : 'Bearish momentum',
      });
    }

    // Volatility
    const volatility = standardDeviation(closes.slice(-20));
    indicators.push({
      name: 'Volatility (20d)',
      value: volatility,
      signal: 'hold',
      description: volatility > mean(closes) * 0.02 ? 'High volatility' : 'Normal volatility',
    });

    return indicators;
  }

  /**
   * Predict future price using multiple methods
   */
  async predictPrice(
    symbol: string,
    historicalData: StockHistoricalData[],
    timeframe: '1d' | '1w' | '1m' | '3m' = '1d'
  ): Promise<StockPrediction> {
    if (historicalData.length < 10) {
      throw new Error('Insufficient historical data for prediction');
    }

    const closes = historicalData.map(d => d.close).reverse();
    const prices = closes.slice(-50); // Use last 50 data points

    // Method 1: Linear regression
    const linearPred = this.linearRegressionPrediction(prices, timeframe);

    // Method 2: Moving average trend
    const maPred = this.movingAveragePrediction(prices, timeframe);

    // Method 3: ML model prediction (if available)
    let mlPred = linearPred;
    if (this.model && prices.length >= 10) {
      try {
        mlPred = await this.mlPrediction(prices, timeframe);
      } catch (error) {
        console.error('ML prediction failed, using linear regression:', error);
      }
    }

    // Combine predictions (weighted average)
    const predictedPrice = (linearPred * 0.4 + maPred * 0.3 + mlPred * 0.3);
    const currentPrice = prices[prices.length - 1];
    const change = predictedPrice - currentPrice;
    const changePercent = (change / currentPrice) * 100;

    // Calculate confidence based on data quality and volatility
    const confidence = this.calculateConfidence(prices, historicalData.length);

    // Determine trend
    const trend: 'bullish' | 'bearish' | 'neutral' = 
      changePercent > 2 ? 'bullish' : 
      changePercent < -2 ? 'bearish' : 
      'neutral';

    // Generate reasons
    const reasons = this.generateReasons(historicalData, changePercent, trend);

    return {
      symbol,
      predictedPrice: Math.round(predictedPrice * 100) / 100,
      confidence: Math.round(confidence * 100) / 100,
      predictionDate: new Date().toISOString(),
      timeframe,
      trend,
      reasons,
    };
  }

  /**
   * Linear regression prediction
   */
  private linearRegressionPrediction(prices: number[], timeframe: '1d' | '1w' | '1m' | '3m'): number {
    const days = timeframe === '1d' ? 1 : timeframe === '1w' ? 7 : timeframe === '1m' ? 30 : 90;
    const x = prices.map((_, i) => i);
    const regression = linearRegression([x, prices]);
    const futureX = prices.length + days - 1;
    return regression.m * futureX + regression.b;
  }

  /**
   * Moving average prediction
   */
  private movingAveragePrediction(prices: number[], timeframe: '1d' | '1w' | '1m' | '3m'): number {
    const shortMA = this.calculateSMA(prices.slice(-10), 10) || prices[prices.length - 1];
    const longMA = this.calculateSMA(prices, prices.length) || prices[prices.length - 1];
    const trend = shortMA - longMA;
    const days = timeframe === '1d' ? 1 : timeframe === '1w' ? 7 : timeframe === '1m' ? 30 : 90;
    return prices[prices.length - 1] + (trend / 10) * days;
  }

  /**
   * ML model prediction
   */
  private async mlPrediction(prices: number[], _timeframe: '1d' | '1w' | '1m' | '3m'): Promise<number> {
    if (!this.model || prices.length < 10) {
      return prices[prices.length - 1];
    }

    // Prepare input (last 10 prices)
    const input = prices.slice(-10);
    const normalized = this.normalize(input);
    const tensor = tf.tensor2d([normalized]);

    try {
      const prediction = this.model.predict(tensor) as tf.Tensor;
      const predValue = await prediction.data();
      const denormalized = this.denormalize([predValue[0]], input);
      prediction.dispose();
      tensor.dispose();
      return denormalized[0];
    } catch (error) {
      return prices[prices.length - 1];
    }
  }

  /**
   * Calculate RSI
   */
  private calculateRSI(prices: number[], period: number = 14): number {
    if (prices.length < period + 1) return 50;

    const changes = [];
    for (let i = 1; i < prices.length; i++) {
      changes.push(prices[i] - prices[i - 1]);
    }

    const gains = changes.filter(c => c > 0);
    const losses = changes.filter(c => c < 0).map(c => Math.abs(c));

    if (losses.length === 0) return 100;
    if (gains.length === 0) return 0;

    const avgGain = mean(gains.slice(-period));
    const avgLoss = mean(losses.slice(-period));

    if (avgLoss === 0) return 100;

    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  }

  /**
   * Calculate Simple Moving Average
   */
  private calculateSMA(prices: number[], period: number): number | null {
    if (prices.length < period) return null;
    const slice = prices.slice(-period);
    return mean(slice);
  }

  /**
   * Calculate MACD
   */
  private calculateMACD(prices: number[]): { value: number; signal: number } | null {
    if (prices.length < 26) return null;

    const ema12 = this.calculateEMA(prices, 12);
    const ema26 = this.calculateEMA(prices, 26);
    
    if (!ema12 || !ema26) return null;

    const macdLine = ema12 - ema26;
    const signalLine = macdLine * 0.9; // Simplified signal line

    return { value: macdLine, signal: signalLine };
  }

  /**
   * Calculate EMA
   */
  private calculateEMA(prices: number[], period: number): number | null {
    if (prices.length < period) return null;

    const multiplier = 2 / (period + 1);
    let ema = mean(prices.slice(0, period));

    for (let i = period; i < prices.length; i++) {
      ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
    }

    return ema;
  }

  /**
   * Normalize data for ML
   */
  private normalize(data: number[]): number[] {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min;
    if (range === 0) return data.map(() => 0.5);
    return data.map(v => (v - min) / range);
  }

  /**
   * Denormalize data from ML
   */
  private denormalize(data: number[], original: number[]): number[] {
    const min = Math.min(...original);
    const max = Math.max(...original);
    const range = max - min;
    return data.map(v => v * range + min);
  }

  /**
   * Calculate prediction confidence
   */
  private calculateConfidence(prices: number[], dataPoints: number): number {
    const volatility = standardDeviation(prices.slice(-20));
    const avgPrice = mean(prices);
    const volatilityPercent = (volatility / avgPrice) * 100;

    // More data points = higher confidence
    const dataConfidence = Math.min(dataPoints / 100, 1) * 50;

    // Lower volatility = higher confidence
    const volatilityConfidence = Math.max(0, 50 - volatilityPercent * 2);

    return Math.min(95, dataConfidence + volatilityConfidence);
  }

  /**
   * Generate prediction reasons
   */
  private generateReasons(
    historicalData: StockHistoricalData[],
    changePercent: number,
    trend: 'bullish' | 'bearish' | 'neutral'
  ): string[] {
    const reasons: string[] = [];
    const recent = historicalData.slice(-5);
    const volumes = recent.map(d => d.volume);
    const avgVolume = mean(volumes);

    if (changePercent > 0) {
      reasons.push(`Positive price momentum detected`);
      if (recent[recent.length - 1].volume > avgVolume * 1.2) {
        reasons.push(`Increasing volume suggests strong interest`);
      }
    } else {
      reasons.push(`Negative price momentum detected`);
      if (recent[recent.length - 1].volume > avgVolume * 1.2) {
        reasons.push(`High selling volume indicates pressure`);
      }
    }

    if (trend === 'bullish') {
      reasons.push(`Technical indicators suggest upward trend`);
    } else if (trend === 'bearish') {
      reasons.push(`Technical indicators suggest downward trend`);
    } else {
      reasons.push(`Mixed signals - market is consolidating`);
    }

    return reasons;
  }
}

export const predictionService = PredictionService.getInstance();

