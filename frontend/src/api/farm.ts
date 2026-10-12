import api from './axios';
import type { FarmCreate, FarmResponse } from '../types';

export const farmAPI = {
  getFarms: () => {
    return api.get<FarmResponse[]>('/farms/');
  },

  getFarm: (farmId: number) => {
    return api.get<FarmResponse>(`/farms/${farmId}`);
  },

  createFarm: (farm: FarmCreate) => {
    return api.post<FarmResponse>('/farms/', farm);
  },
};

export default farmAPI;
