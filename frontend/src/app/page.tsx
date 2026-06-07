// src/app/page.tsx
"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { dashboardService } from "@/services/api";
import { DashboardMetricsResponse } from "@/types";
import { Activity, ShieldAlert, ChevronDown, ChevronUp, Terminal, FileCode } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { FuzzSandbox } from "@/components/dashboard/fuzz-sandbox";
import { JsonView, defaultStyles } from "react-json-view-lite";
import "react-json-view-lite/dist/index.css";

export default function Dashboard() {
  const [data, setData] = useState<DashboardMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);
  const initialLoadRef = useRef(false);

  const loadDashboard = useCallback(async (isBackground = false) => {
    try {
      const metrics = await dashboardService.getMetrics();
      setData(metrics);
      setError(null);
    } catch (err) {
      if (!isBackground) {
        setError("Failed to connect to Intercept Backend or Supabase.");
      }
    } finally {
      if (!isBackground) {
        setLoading(false);
      }
    }
  }, []);

  // First initialization load
  useEffect(() => {
    if (!initialLoadRef.current) {
      loadDashboard(false);
      initialLoadRef.current = true;
    }
  }, [loadDashboard]);

  // Automated background polling loop for real-time async telemetry updates
  useEffect(() => {
    const pollInterval = setInterval(() => {
      loadDashboard(true);
    }, 4000); // Evaluates state changes every 4 seconds cleanly

    return () => clearInterval(pollInterval);
  }, [loadDashboard]);

  if (loading) return <div className="flex h-screen items-center justify-center"><Activity className="animate-spin text-blue-500 w-8 h-8" /></div>;
  if (error || !data) return <div className="flex h-screen items-center justify-center text-red-500"><ShieldAlert className="mr-2 w-6 h-6"/>{error}</div>;

  const recentSessions = Array.isArray(data?.recent_sessions) ? data.recent_sessions : [];
  
  const chartData = [...recentSessions].reverse().map((session, index) => ({
    name: `Run ${index + 1}`,
    failures: session?.failed ?? session?.failed_tests ?? 0,
    passes: session?.passed ?? session?.passed_tests ?? 0
  }));

  const toggleRow = (id: string) => {
    setExpandedSessionId(expandedSessionId === id ? null : id);
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Intercept Telemetry</h1>
            <p className="text-slate-500 mt-1">Live AI Contract Monitoring</p>
          </div>
        </header>

        {/* Top Metrics Row */}
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

        <FuzzSandbox onRunComplete={() => loadDashboard(true)} />

        {/* Analytics Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">Pipeline Failure Trends</h2>
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

        {/* Expanded Security Audit Ledger */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-slate-900">Security Audit Ledger</h2>
            <p className="text-slate-400 text-xs mt-1">Click any row to inspect breaking payloads and contract metadata</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="w-10 px-6 py-3"></th>
                  <th className="px-6 py-3 font-semibold text-slate-700">Timestamp</th>
                  <th className="px-6 py-3 font-semibold text-slate-700">Schema Target</th>
                  <th className="px-6 py-3 font-semibold text-slate-700">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentSessions.map((session: any, i: number) => {
                  const rowId = session.id || String(i);
                  const isExpanded = expandedSessionId === rowId;
                  
                  return (
                    <tr key={`group-${rowId}`} className="contents">
                      <td 
                        className="hover:bg-slate-50/80 cursor-pointer transition-colors px-6 py-4 text-slate-400"
                        onClick={() => toggleRow(rowId)}
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-500 cursor-pointer" onClick={() => toggleRow(rowId)}>
                        {session?.created_at ? new Date(session.created_at).toLocaleString() : new Date().toLocaleString()}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-900 cursor-pointer" onClick={() => toggleRow(rowId)}>{session?.schema_name || 'Dynamic Schema'}</td>
                      <td className="px-6 py-4 cursor-pointer" onClick={() => toggleRow(rowId)}>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          (session.result === 'passed' || session.status === 'passed') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {(session.result || session.status || 'FAILED').toUpperCase()}
                        </span>
                      </td>

                      {/* Expanded Split-Pane Diff Section */}
                     {/* Expanded Split-Pane Diff & Analysis Section */}
                      {isExpanded && (
                        <tr className="bg-slate-900 border-t border-b border-slate-700">
                          <td colSpan={4} className="p-6">
                            
                            {/* PREMIUM UPGRADE: AI Security Analysis Banner */}
                            {session.result === 'failed' && (
                              <div className="mb-6 bg-indigo-950/40 border border-indigo-500/30 rounded-xl p-5 shadow-inner">
                                <div className="flex items-center mb-3">
                                  <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center mr-3 border border-indigo-500/50">
                                    <span className="text-indigo-400 text-lg">✨</span>
                                  </div>
                                  <h3 className="text-indigo-300 font-bold text-sm tracking-wide uppercase">AI Root Cause Analysis & Remediation</h3>
                                </div>
                                <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-sans pl-11">
                                  {session.ai_analysis}
                                </div>
                              </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-200">
                              {/* Left Panel: Expected Schema Structure */}
                              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-blue-500/50"></div>
                                <div className="flex items-center text-slate-400 font-medium text-xs uppercase tracking-wider pb-2 border-b border-slate-800">
                                  <FileCode className="w-4 h-4 mr-2 text-blue-400" />
                                  Target Contract (Expected)
                                </div>
                                <div className="font-mono text-xs overflow-auto max-h-72 pt-2 text-blue-300">
                                  {session?.schema_definition ? (
                                    <JsonView data={session.schema_definition} style={defaultStyles} />
                                  ) : (
                                    <pre className="text-slate-500">No static model definition provided.</pre>
                                  )}
                                </div>
                              </div>

                              {/* Right Panel: The Poisoned Adversarial Payload */}
                              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-red-500/50"></div>
                                <div className="flex items-center text-slate-400 font-medium text-xs uppercase tracking-wider pb-2 border-b border-slate-800">
                                  <Terminal className="w-4 h-4 mr-2 text-red-400" />
                                  Adversarial Payloads Caught
                                </div>
                                <div className="font-mono text-xs overflow-auto max-h-72 pt-2 text-red-300">
                                  {session?.details && session.details.length > 0 ? (
                                    <div className="space-y-4">
                                      {session.details.map((det: any, idx: number) => (
                                        <div key={idx} className="pb-4 border-b border-slate-800/50 last:border-0">
                                          <div className="flex justify-between items-center mb-2">
                                            <span className="text-slate-500 text-[10px] font-bold tracking-wider bg-slate-900 px-2 py-1 rounded">ATTACK #{idx + 1}</span>
                                            <span className={`text-[10px] font-bold px-2 py-1 rounded ${det?.status === 'passed' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                                              {det?.status?.toUpperCase()}
                                            </span>
                                          </div>
                                          
                                          <p className="text-slate-400 text-[10px] mb-1">INJECTED JSON:</p>
                                          <p className="bg-slate-900/80 p-3 rounded-md border border-slate-800 whitespace-pre-wrap text-emerald-400/80">
                                            {typeof det?.user_input === 'string' ? det.user_input : JSON.stringify(det?.user_input, null, 2)}
                                          </p>
                                          
                                          {det?.error && (
                                            <div className="mt-2">
                                              <p className="text-red-500/80 text-[10px] mb-1 font-bold">SYSTEM CRASH TRACE:</p>
                                              <p className="text-red-400 text-[11px] font-sans bg-red-950/20 border border-red-900/30 px-3 py-2 rounded-md">
                                                {det.error}
                                              </p>
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <pre className="text-slate-500">No test trace logs recorded for this session execution.</pre>
                                  )}
                                </div>
                              </div>

                            </div>
                          </td>
                        </tr>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>
  );
}