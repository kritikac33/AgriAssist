import api from './axios';
import type { UserResponse, LoginRequest, UserCreate, Token } from '../types';

export const authAPI = {
  login: (credentials: LoginRequest) => {
    return api.post<Token>('/auth/login', credentials);
  },

  register: (data: UserCreate) => {
    return api.post<UserResponse>('/auth/register', data);
  },

  getMe: () => {
    return api.get<UserResponse>('/auth/me');
  },
};

export default authAPI;
