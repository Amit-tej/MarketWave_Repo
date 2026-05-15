import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'
const client = axios.create({baseURL: API_BASE, timeout: 30_000})

export async function fetchMarkets(){
  const r = await client.get('/markets')
  return r.data
}

export async function fetchCommodities(market: string){
  const r = await client.get(`/markets/${encodeURIComponent(market)}/commodities`)
  return r.data
}

export async function postPredict(body: {market:string, commodity:string, horizon:number}){
  const r = await client.post('/predict-mistral', body)
  return r.data
}

export async function postPredictMistral(body: {market:string, commodity:string, horizon:number}){
  const r = await client.post('/predict-mistral', body)
  return r.data
}

export async function fetchExplain(prediction_id: string){
  const r = await client.get(`/predictions/${encodeURIComponent(prediction_id)}/explain`)
  return r.data
}

export async function fetchPriceComparison(commodity: string){
  const r = await client.get(`/price-comparison/${encodeURIComponent(commodity)}`)
  return r.data
}

export default client
