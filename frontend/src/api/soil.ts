import api from './axios';
import type { SoilRecordCreate, SoilRecordResponse, SoilAnalysis } from '../types';

export const soilAPI = {
  createSoilRecord: (data: SoilRecordCreate) => {
    return api.post<SoilRecordResponse>('/soil-records/', data);
  },

  getSoilRecords: (farmId?: number) => {
    const params = farmId ? { farm_id: farmId } : {};
    return api.get<SoilRecordResponse[]>('/soil-records/', { params });
  },

  analyzeSoil: (id: number, cropName: string) => {
    return api.get<SoilAnalysis>(`/soil-records/${id}/analyze`, { params: { crop_name: cropName } });
  },
};

export default soilAPI;
