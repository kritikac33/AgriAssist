import api from './axios';

export interface BuyerDashboardData {
  buyer_name: string;
  active_orders: number;
  awaiting_payment: number;
  in_fulfillment: number;
  delivered_orders: number;
  paid_purchase_value: string;
  order_count: number;
  message_count: number;
  cart_item_count: number;
  saved_listing_count: number;
  unread_message_count: number | null;
  unread_tracking_available: boolean;
}

export interface CartItem {
  id: number;
  listing_id: number;
  quantity_quintals: string;
  available: boolean;
  subtotal: string;
  listing: {
    id: number;
    crop_name: string;
    quantity_quintals: string;
    price_per_quintal: string;
    location: string | null;
    seller_name: string | null;
    seller_id: number;
    status: string;
    description?: string | null;
  } | null;
}

export interface BuyerAddress {
  id: number; label: string; recipient_name: string; phone: string; address_line1: string;
  address_line2?: string | null; city: string; state: string; postal_code: string;
  delivery_instructions?: string | null; is_default: number | boolean;
}

export const buyerAPI = {
  dashboard: async () => (await api.get<BuyerDashboardData>('/buyer/dashboard')).data,
  cart: async () => (await api.get<{ items: CartItem[]; subtotal: string }>('/buyer/cart')).data,
  addToCart: async (listing_id: number, quantity_quintals: number) => { const data = (await api.post('/buyer/cart', { listing_id, quantity_quintals })).data; window.dispatchEvent(new Event('buyer-cart-updated')); return data; },
  updateCart: async (id: number, quantity_quintals: number) => { const data = (await api.patch(`/buyer/cart/${id}`, { quantity_quintals })).data; window.dispatchEvent(new Event('buyer-cart-updated')); return data; },
  removeCartItem: async (id: number) => { const response = await api.delete(`/buyer/cart/${id}`); window.dispatchEvent(new Event('buyer-cart-updated')); return response; },
  clearCart: async () => { const response = await api.delete('/buyer/cart'); window.dispatchEvent(new Event('buyer-cart-updated')); return response; },
  saved: async () => (await api.get<any[]>('/buyer/saved')).data,
  save: async (listingId: number) => api.put(`/buyer/saved/${listingId}`),
  unsave: async (listingId: number) => api.delete(`/buyer/saved/${listingId}`),
  orders: async () => (await api.get<any[]>('/buyer/orders')).data,
  conversations: async () => (await api.get<any[]>('/buyer/conversations')).data,
  addresses: async () => (await api.get<BuyerAddress[]>('/buyer/addresses')).data,
  createAddress: async (payload: Omit<BuyerAddress, 'id'>) => (await api.post<BuyerAddress>('/buyer/addresses', payload)).data,
  updateAddress: async (id: number, payload: Partial<BuyerAddress>) => (await api.patch<BuyerAddress>(`/buyer/addresses/${id}`, payload)).data,
  deleteAddress: async (id: number) => api.delete(`/buyer/addresses/${id}`),
  notifications: async () => (await api.get<any[]>('/buyer/notifications')).data,
  markNotificationRead: async (id: number) => api.post(`/buyer/notifications/${id}/read`),
  createSupportTicket: async (payload: { transaction_id?: number; category: string; description: string }) => (await api.post('/buyer/support', payload)).data,
  supportTickets: async () => (await api.get<any[]>('/buyer/support')).data,
};
