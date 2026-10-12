import api from './axios';
import type { DiagnosisWithTreatment, DiagnosisResponse } from '../types';

export const diseaseAPI = {
  createDiagnosis: (cropId: number, file: File, consent?: boolean) => {
    const formData = new FormData();
    formData.append('crop_id', cropId.toString());
    formData.append('file', file);
    if (consent !== undefined) {
      formData.append('consent', consent.toString());
    }

    return api.post<DiagnosisWithTreatment>('/diagnoses/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getDiagnoses: (cropId?: number) => {
    const params = cropId ? { crop_id: cropId } : {};
    return api.get<DiagnosisResponse[]>('/diagnoses/', { params });
  },

  getDiagnosis: (id: number) => {
    return api.get<DiagnosisWithTreatment>(`/diagnoses/${id}`);
  },
};

export default diseaseAPI;
