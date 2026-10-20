import api from './axios';

export interface Transaction {
  id: number;
  listing_id: number | null;
  buyer_id: number | null;
  seller_id: number | null;
  razorpay_order_id: string | null;
  razorpay_payment_id: string | null;
  razorpay_key_id?: string | null;
  quantity_quintals: string;
  total_amount: string;
  status: string;
  transaction_date: string;
  created_at: string;
  updated_at: string;
  fulfillment_status?: string;
  delivery_method?: string | null;
  crop_name_snapshot?: string | null;
  cancellation_requested_at?: string | null;
  cancellation_reason?: string | null;
}

export const transactionsAPI = {
  createTransaction: async (listingId: number, quantity?: number, checkout?: { delivery_method: 'pickup' | 'delivery'; delivery_address_id?: number; delivery_instructions?: string }): Promise<Transaction> => {
    const response = await api.post<Transaction>('/transactions', { listing_id: listingId, quantity_quintals: quantity, ...checkout });
    return response.data;
  },

  verifyTransaction: async (id: number, payment: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }): Promise<Transaction> => {
    const response = await api.post<Transaction>(`/transactions/${id}/verify`, payment);
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
  cancelUnpaid: async (id: number) => (await api.post<Transaction>(`/transactions/${id}/cancel`)).data,
  requestCancellation: async (id: number, reason: string) => (await api.post<Transaction>(`/transactions/${id}/cancellation-request`, { reason })).data,
  updateFulfillment: async (id: number, fulfillment_status: string) => (await api.patch<Transaction>(`/transactions/${id}/fulfillment`, { fulfillment_status })).data,
};
