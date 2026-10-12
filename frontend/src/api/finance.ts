import api from './axios';

export interface FinanceEntry {
  id: number;
  farm_id: number;
  entry_type: string;
  category: string;
  amount: string;
  date: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinanceSummary {
  farm_id: number;
  total_income: string;
  total_expenses: string;
  net_profit: string;
  category_breakdown: Record<string, unknown>;
  monthly_breakdown: Record<string, unknown>;
}

export const financeAPI = {
  createEntry: async (data: Partial<FinanceEntry>): Promise<FinanceEntry> => {
    const response = await api.post<FinanceEntry>('/finance-entries/', data);
    return response.data;
  },

  getEntries: async (params?: {
    farm_id?: number;
    entry_type?: 'income' | 'expense';
    start_date?: string;
    end_date?: string;
  }): Promise<FinanceEntry[]> => {
    const response = await api.get<FinanceEntry[]>('/finance-entries/', { params });
    return response.data;
  },

  getEntry: async (id: number): Promise<FinanceEntry> => {
    const response = await api.get<FinanceEntry>(`/finance-entries/${id}`);
    return response.data;
  },

  getSummary: async (farmId?: number): Promise<FinanceSummary> => {
    const params = farmId ? { farm_id: farmId } : {};
    const response = await api.get<FinanceSummary>('/finance-entries/summary', { params });
    return response.data;
  },
};
