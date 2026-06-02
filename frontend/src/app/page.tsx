// src/app/page.tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { dashboardService } from "@/services/api";
import { DashboardMetricsResponse } from "@/types";
import { Activity, ShieldAlert } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
// Import our new Sandbox
import { FuzzSandbox } from "@/components/dashboard/fuzz-sandbox";

export default function Dashboard() {
  const [data, setData] = useState<DashboardMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // We wrap this in useCallback so the Sandbox can trigger a refresh
  const loadDashboard = useCallback(async () => {
    try {
      const metrics = await dashboardService.getMetrics();
      setData(metrics);
      setError(null);
    } catch (err) {
      setError("Failed to connect to Intercept Backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) return <div className="flex h-screen items-center justify-center"><Activity className="animate-spin text-blue-500" /></div>;
  if (error || !data) return <div className="flex h-screen items-center justify-center text-red-500"><ShieldAlert className="mr-2"/>{error}</div>;

  const chartData = [...data.recent_sessions].reverse().map((session, index) => ({
    name: `Run ${index + 1}`,
    failures: session.failed,
    passes: session.passed
  }));

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Intercept Telemetry</h1>
            <p className="text-slate-500 mt-1">Live AI Contract Monitoring</p>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Total Tests Monitored</p>
            <p className="text-4xl font-bold text-slate-900 mt-2">{data.total_tests_tracked}</p>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Global Failure Rate</p>
            <p className="text-4xl font-bold text-red-600 mt-2">{data.global_failure_rate}%</p>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Active Repositories</p>
            <p className="text-4xl font-bold text-slate-900 mt-2">1</p>
          </div>
        </div>

        {/* Mount the Live Fuzzing Sandbox Here */}
        <FuzzSandbox onRunComplete={loadDashboard} />

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">Recent Fuzzing Sessions</h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="failures" stroke="#EF4444" strokeWidth={3} name="Failed Contracts" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </main>
  );
}