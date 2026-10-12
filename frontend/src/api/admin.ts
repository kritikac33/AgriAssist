import api from './axios';

export interface DashboardStats {
  total_users: number;
  users_by_role: Record<string, unknown>;
  total_diagnoses: number;
  low_confidence_diagnoses: number;
  top_diseases: unknown[];
  active_alerts: number;
  total_listings: number;
  open_listings: number;
  closed_listings: number;
  total_transaction_volume: string;
  total_farms: number;
}

export interface SystemConfig {
  id: number;
  config_key: string;
  config_value: string | null;
  description: string | null;
  updated_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  details: string | null;
  ip_address: string | null;
  created_at: string;
}

export const adminAPI = {
  getDashboard: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/admin/dashboard');
    return response.data;
  },

  getConfig: async (): Promise<SystemConfig[]> => {
    const response = await api.get<SystemConfig[]>('/admin/config');
    return response.data;
  },

  updateConfig: async (configKey: string, configValue: string): Promise<SystemConfig> => {
    const response = await api.patch<SystemConfig>(`/admin/config/${configKey}`, { config_value: configValue });
    return response.data;
  },

  getUsers: async (params?: {
    search?: string;
    role?: string;
  }): Promise<any[]> => {
    const response = await api.get<any[]>('/admin/users', { params });
    return response.data;
  },

  getAuditLogs: async (limit?: number): Promise<AuditLog[]> => {
    const params = limit ? { limit } : {};
    const response = await api.get<AuditLog[]>('/admin/audit-logs', { params });
    return response.data;
  },
};
