import api from './axios';
import type { YieldPredictionCreate, YieldPredictionResponse } from '../types';

export const yieldAPI = {
  createPrediction: (data: YieldPredictionCreate) => {
    return api.post<YieldPredictionResponse>('/yield-predictions/', data);
  },

  getPredictions: (farmId?: number, cropId?: number) => {
    const params: any = {};
    if (farmId) params.farm_id = farmId;
    if (cropId) params.crop_id = cropId;
    return api.get<YieldPredictionResponse[]>('/yield-predictions/', { params });
  },

  getPrediction: (id: number) => {
    return api.get<YieldPredictionResponse>(`/yield-predictions/${id}`);
  },

  getHistory: (cropId: number) => {
    return api.get<YieldPredictionResponse[]>(`/yield-predictions/crop/${cropId}/history`);
  },
};

export default yieldAPI;
