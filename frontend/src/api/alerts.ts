import api from './axios';

export interface OutbreakAlert {
  id: number;
  disease_name: string;
  region_description: string;
  center_latitude: string;
  center_longitude: string;
  radius_km: string;
  severity: 'low' | 'medium' | 'high';
  case_count: number;
  preventive_measures: string | null;
  is_active: boolean;
  created_at: string;
  retracted_at?: string;
}

export const alertsAPI = {
  getAlerts: async (lat?: number, lon?: number): Promise<OutbreakAlert[]> => {
    const params: any = {};
    if (lat !== undefined) params.lat = lat;
    if (lon !== undefined) params.lon = lon;
    const response = await api.get<OutbreakAlert[]>('/alerts/', { params });
    return response.data;
  },

  createAlert: async (data: Partial<OutbreakAlert>): Promise<OutbreakAlert> => {
    const response = await api.post<OutbreakAlert>('/alerts/', {
      ...data,
      center_latitude: data.center_latitude !== undefined ? String(data.center_latitude) : undefined,
      center_longitude: data.center_longitude !== undefined ? String(data.center_longitude) : undefined,
      radius_km: data.radius_km !== undefined ? String(data.radius_km) : undefined,
    });
    return response.data;
  },

  retractAlert: async (id: number): Promise<OutbreakAlert> => {
    const response = await api.patch<OutbreakAlert>(`/alerts/${id}/retract`);
    return response.data;
  },
};
