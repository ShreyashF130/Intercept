// src/services/api.ts
import axios from 'axios';
import { DashboardMetricsResponse } from '@/types';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
const INTERCEPT_API_KEY = "sk_test_intercept_123";
export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': INTERCEPT_API_KEY,
    },
});

export const dashboardService = {
    getMetrics: async (): Promise<DashboardMetricsResponse> => {
        const response = await apiClient.get('/dashboard/metrics');
        return response.data;
    },
    
    // NEW: Function to trigger a live fuzz session from the browser
    triggerFuzzSession: async (schemaName: string, schemaDefinition: any) => {
        const response = await apiClient.post('/fuzz/run', {
            schema_name: schemaName,
            schema_definition: schemaDefinition
        });
        return response.data;
    }
};