import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchHistorical, createPrediction, getExplain } from '../utils/api'
import { PredictionResponse, ExplainResponse, HistoricalData } from '../types'

export function useHistorical(market:string, commodity:string, days=30){
  return useQuery<HistoricalData>({
    queryKey: ['historical', market, commodity, days],
    queryFn: ()=> fetchHistorical(market, commodity, days),
    staleTime: 60_000,
    enabled: !!market && !!commodity
  })
}

export function usePredict(){
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({market,commodity,horizon}:{market:string,commodity:string,horizon:number})=> createPrediction(market, commodity, horizon),
    onSuccess: (data: PredictionResponse)=>{
      qc.setQueryData(['prediction', data.prediction_id], data)
    }
  })
}

export function useExplain(predictionId?: string){
  return useQuery<ExplainResponse>({
    queryKey: ['explain', predictionId],
    queryFn: ()=> getExplain(predictionId || ''),
    enabled: !!predictionId
  })
}
