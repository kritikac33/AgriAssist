import api from './axios';
import type { IrrigationScheduleCreate, IrrigationScheduleResponse } from '../types';

export const irrigationAPI = {
  createSchedule: (data: IrrigationScheduleCreate) => {
    return api.post<IrrigationScheduleResponse>('/irrigation-schedules/', data);
  },

  getSchedules: (farmId?: number, statusFilter?: string) => {
    const params: any = {};
    if (farmId) params.farm_id = farmId;
    if (statusFilter) params.status_filter = statusFilter;
    return api.get<IrrigationScheduleResponse[]>('/irrigation-schedules/', { params });
  },

  recalculateSchedule: (id: number) => {
    return api.post<IrrigationScheduleResponse>(`/irrigation-schedules/${id}/recalculate`);
  },

  postponeSchedule: (id: number, days?: number) => {
    const params = days ? { days } : {};
    return api.post<IrrigationScheduleResponse>(`/irrigation-schedules/${id}/postpone`, {}, { params });
  },
};

export default irrigationAPI;
