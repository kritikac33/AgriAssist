import api from './axios';

export interface Transaction {
  id: number;
  listing_id: number | null;
  buyer_id: number | null;
  seller_id: number | null;
  razorpay_order_id: string | null;
  razorpay_payment_id: string | null;
  quantity_quintals: string;
  total_amount: string;
  status: string;
  transaction_date: string;
  created_at: string;
  updated_at: string;
}

export const transactionsAPI = {
  createTransaction: async (listingId: number): Promise<Transaction> => {
    const response = await api.post<Transaction>('/transactions', { listing_id: listingId });
    return response.data;
  },

  verifyTransaction: async (id: number): Promise<Transaction> => {
    const response = await api.get<Transaction>(`/transactions/${id}/verify`);
    return response.data;
  },

  updateTransactionStatus: async (id: number, status: string): Promise<Transaction> => {
    const response = await api.patch<Transaction>(`/transactions/${id}/status`, { status });
    return response.data;
  },

  getTransactions: async (): Promise<Transaction[]> => {
    const response = await api.get<Transaction[]>('/transactions');
    return response.data;
  },

  getTransaction: async (id: number): Promise<Transaction> => {
    const response = await api.get<Transaction>(`/transactions/${id}`);
    return response.data;
  },
};
