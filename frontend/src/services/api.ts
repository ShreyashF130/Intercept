// src/services/api.ts
import axios from 'axios';
import { DashboardMetricsResponse } from '@/types';

// 1. Point dynamically to Render (fallback to localhost only for local dev)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://intercept-bugf.onrender.com/api/v1';

// 2. Use the newly seeded Supabase Tenant Key
const INTERCEPT_API_KEY = process.env.NEXT_PUBLIC_INTERCEPT_API_KEY || 'sk_intercept_test_99x77v';

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
    
    // 3. Update payload to support your BYOK Multi-Provider Backend
    triggerFuzzSession: async (schemaName: string, schemaDefinition: any) => {
        // NOTE: For a production Sandbox, you will want users to input their own keys in the UI.
        // For this V1 prototype, we inject your default Gemini key so the Sandbox actually runs.
        const fallbackProvider = process.env.NEXT_PUBLIC_DEFAULT_LLM_PROVIDER || "gemini";
        const fallbackKey = process.env.NEXT_PUBLIC_DEFAULT_LLM_KEY || "AIzaSyYourActualWorkingGeminiKeyHere";

        const response = await apiClient.post('/fuzz/run', {
            schema_name: schemaName,
            schema_definition: schemaDefinition,
            llm_provider: fallbackProvider,
            llm_api_key: fallbackKey
        });
        return response.data;
    }
};