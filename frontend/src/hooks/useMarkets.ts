import { useQuery } from '@tanstack/react-query'
import { getMarkets, getCommodities } from '../utils/api'
import { MarketsResponse, CommoditiesResponse } from '../types'

export function useMarkets(){
  return useQuery<MarketsResponse>({
    queryKey: ['markets'],
    queryFn: getMarkets,
    staleTime: 60_000
  })
}

export function useCommodities(market?: string){
  return useQuery<CommoditiesResponse>({
    queryKey: ['commodities', market],
    queryFn: ()=> getCommodities(market || ''),
    enabled: !!market,
    staleTime: 60_000
  })
}
