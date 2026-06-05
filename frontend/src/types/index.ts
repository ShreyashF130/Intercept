// src/types/index.ts

export interface TestCaseResult {
    test_id: number;
    input_fired: string;
    engine_status: 'passed' | 'failed' | 'error';
    model_output: any;
    validation_errors: any;
}

// frontend/src/types/index.ts (or your types file)

export interface FuzzSessionHistory {
  id?: string;
  schema_name: string;
  status: string;         // 'processing', 'completed', 'failed'
  result?: string;        // 'passed', 'failed'
  created_at?: string;
  
  // --- ADD THESE NEW MULTI-TENANT TRACKING KEYS ---
  total_tests?: number;
  passed_tests?: number;
  failed_tests?: number;

  // Keep these if your older dashboard logic still references them
  failed?: number;
  passed?: number;
}

// Ensure your main response wrapper mirrors this array type cleanly
export interface DashboardMetricsResponse {
  total_tests_tracked: number;
  global_failure_rate: number;
  recent_sessions: FuzzSessionHistory[]; // <-- Maps cleanly here
}