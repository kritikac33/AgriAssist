import api from './axios';

export interface Scheme {
  id: number;
  name: string;
  description: string | null;
  eligibility_criteria: string | null;
  min_land_hectares: string | null;
  max_land_hectares: string | null;
  eligible_crops: string | null;
  eligible_states: string | null;
  benefits: string | null;
  application_link: string | null;
  deadline: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SchemeMatch {
  scheme_id: number;
  scheme_name: string;
  eligibility_reason: string;
  benefits: string | null;
  application_link: string | null;
  deadline: string | null;
}

export const schemesAPI = {
  getSchemes: async (): Promise<Scheme[]> => {
    const response = await api.get<Scheme[]>('/schemes');
    return response.data;
  },

  getScheme: async (id: number): Promise<Scheme> => {
    const response = await api.get<Scheme>(`/schemes/${id}`);
    return response.data;
  },

  getMatches: async (farmId: number, cropName?: string, state?: string): Promise<SchemeMatch[]> => {
    const response = await api.post<SchemeMatch[]>('/schemes/matches', {
      farm_id: farmId,
      crop_name: cropName,
      state: state
    });
    return response.data;
  },
};
