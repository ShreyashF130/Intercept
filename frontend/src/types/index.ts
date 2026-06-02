// src/types/index.ts

export interface TestCaseResult {
    test_id: number;
    input_fired: string;
    engine_status: 'passed' | 'failed' | 'error';
    model_output: any;
    validation_errors: any;
}

export interface FuzzSessionHistory {
    id: number;
    repository: string;
    date: string;
    passed: number;
    failed: number;
}

export interface DashboardMetricsResponse {
    status: string;
    global_failure_rate: number;
    total_tests_tracked: number;
    recent_sessions: FuzzSessionHistory[];
}