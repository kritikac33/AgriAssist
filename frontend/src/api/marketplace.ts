import api from './axios';

export interface Listing {
  id: number;
  seller_id: number;
  seller_name?: string | null;
  crop_name: string;
  quantity_quintals: string;
  price_per_quintal: string;
  unit: string;
  location: string | null;
  description?: string | null;
  latitude: string | null;
  longitude: string | null;
  photo_path: string | null;
  status: string;
  market_price_benchmark: string | null;
  price_label: string | null;
  market_price_updated: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  listing_id: number;
  sender_id: number;
  buyer_id?: number | null;
  sender_name?: string | null;
  content: string;
  created_at: string;
}

export const marketplaceAPI = {
  getListings: async (params?: {
    crop?: string;
    min_price?: number;
    max_price?: number;
    min_quantity?: number;
    seller?: string;
    limit?: number;
    offset?: number;
    lat?: number;
    lon?: number;
    sort_by?: string;
  }): Promise<Listing[]> => {
    const response = await api.get<Listing[]>('/listings', { params });
    return response.data;
  },

  getListing: async (id: number): Promise<Listing> => {
    const response = await api.get<Listing>(`/listings/${id}`);
    return response.data;
  },

  createListing: async (data: Partial<Listing>): Promise<Listing> => {
    const response = await api.post<Listing>('/listings', data);
    return response.data;
  },

  updateListing: async (id: number, data: Partial<Listing>): Promise<Listing> => {
    const response = await api.patch<Listing>(`/listings/${id}`, data);
    return response.data;
  },

  getMessages: async (listingId: number): Promise<Message[]> => {
    const response = await api.get<Message[]>(`/listings/${listingId}/messages`);
    return response.data;
  },

  sendMessage: async (listingId: number, content: string): Promise<Message> => {
    const response = await api.post<Message>(`/listings/${listingId}/messages`, { content });
    return response.data;
  },
};
