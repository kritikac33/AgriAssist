import api from './axios';
import type { CropCreate, CropResponse } from '../types';

export const cropAPI = {
  getCrops: (farmId?: number) => {
    const params = farmId ? { farm_id: farmId } : {};
    return api.get<CropResponse[]>('/crops/', { params });
  },

  getCrop: (cropId: number) => {
    return api.get<CropResponse>(`/crops/${cropId}`);
  },

  createCrop: (crop: CropCreate) => {
    return api.post<CropResponse>('/crops/', crop);
  },
};

export default cropAPI;
