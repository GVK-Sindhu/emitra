import axios from 'axios';

// Default organization ID resolved during database seeding
const DEFAULT_ORG_ID = import.meta.env.VITE_ORG_ID || '3d98e046-70ca-4ebe-9b1f-03244b591b3b';

const getBaseURL = () => {
  let url = import.meta.env.VITE_API_URL;
  if (url) {
    url = url.trim().replace(/\/+$/, '');
    if (!url.endsWith('/api')) {
      url = `${url}/api`;
    }
    return url;
  }
  return '/api';
};

const apiClient = axios.create({
  baseURL: getBaseURL(),
});

// Centralized request interceptor to enforce tenant header injection across all API calls
apiClient.interceptors.request.use(
  (config) => {
    config.headers['X-Organization-ID'] = DEFAULT_ORG_ID;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const api = {
  // 1. Dashboard metrics
  getDashboardStats: async () => {
    const response = await apiClient.get('/emissions/dashboard_stats/');
    return response.data;
  },

  // 2. Emission records listing & updating
  getEmissions: async (params = {}) => {
    const response = await apiClient.get('/emissions/', { params });
    return response.data;
  },

  updateEmission: async (id, data) => {
    const response = await apiClient.patch(`/emissions/${id}/`, data);
    return response.data;
  },

  approveEmission: async (id, reason) => {
    const response = await apiClient.post(`/emissions/${id}/approve/`, {
      change_reason: reason,
      changed_by: 'analyst@acme.com',
    });
    return response.data;
  },

  rejectEmission: async (id, reason) => {
    const response = await apiClient.post(`/emissions/${id}/reject/`, {
      change_reason: reason,
      changed_by: 'analyst@acme.com',
    });
    return response.data;
  },

  approveBatchEmissions: async (ids, reason) => {
    const response = await apiClient.post('/emissions/approve_batch/', {
      record_ids: ids,
      change_reason: reason,
      changed_by: 'analyst@acme.com',
    });
    return response.data;
  },

  // 3. File ingestion
  uploadFile: async (file, sourceType, uploadedBy = 'analyst@acme.com') => {
    const formData = new FormData();
    formData.append('uploaded_file', file);
    formData.append('source_type', sourceType);
    formData.append('uploaded_by', uploadedBy);

    const response = await apiClient.post('/datasources/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getUploads: async () => {
    const response = await apiClient.get('/datasources/');
    return response.data;
  },

  // 4. Audit history
  getAuditLogs: async (emissionRecordId) => {
    const params = emissionRecordId ? { emission_record: emissionRecordId } : {};
    const response = await apiClient.get('/audits/', { params });
    return response.data;
  },
};

export default api;
