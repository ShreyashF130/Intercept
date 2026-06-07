// src/components/dashboard/fuzz-sandbox.tsx
"use client";

import { useState, useEffect } from "react";
import { dashboardService } from "@/services/api";
import { Play, AlertCircle, CheckCircle2 } from "lucide-react";

const STORAGE_KEY = "intercept_sandbox_schema";
const DEFAULT_SCHEMA = `{
  "username": "string",
  "age": "integer",
  "is_active": "boolean"
}`;

export function FuzzSandbox({ onRunComplete }: { onRunComplete: () => void }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'idle' | 'success' | 'error', msg: string }>({ type: 'idle', msg: '' });
  const [schemaInput, setSchemaInput] = useState(DEFAULT_SCHEMA);

  // Load the previously used schema layout on initialization safely
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      setSchemaInput(saved);
    }
  }, []);

  const handleSchemaChange = (value: string) => {
    setSchemaInput(value);
    localStorage.setItem(STORAGE_KEY, value);
  };

  const handleRunFuzzer = async () => {
    setLoading(true);
    setStatus({ type: 'idle', msg: '' });
    
    try {
      // Validate structural safety before deployment
      const parsedSchema = JSON.parse(schemaInput);
      
      const result = await dashboardService.triggerFuzzSession("SandboxSchema", parsedSchema);
      
      setStatus({ 
        type: 'success', 
        msg: `Fuzz payload generated and accepted. Analyzing boundaries asynchronously...` 
      });
      
      // Notify parent wrapper to update ledger
      onRunComplete();
      
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setStatus({ type: 'error', msg: 'Invalid JSON format. Please check your syntax.' });
      } else {
        setStatus({ type: 'error', msg: err.response?.data?.message || 'Failed to connect to the Fuzzing Engine.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mt-8">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Live Fuzzing Sandbox</h2>
        <p className="text-sm text-slate-500">Paste your target JSON schema below to generate live adversarial attacks.</p>
      </div>

      <textarea
        className="w-full h-48 p-4 font-mono text-sm bg-slate-900 text-green-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
        value={schemaInput}
        onChange={(e) => handleSchemaChange(e.target.value)}
        disabled={loading}
      />

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
            {status.type === 'error' && (
                <div className="flex items-center text-red-500 text-sm font-medium">
                    <AlertCircle className="w-4 h-4 mr-1" /> {status.msg}
                </div>
            )}
            {status.type === 'success' && (
                <div className="flex items-center text-emerald-500 text-sm font-medium">
                    <CheckCircle2 className="w-4 h-4 mr-1" /> {status.msg}
                </div>
            )}
        </div>

        <button
          onClick={handleRunFuzzer}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
             <span className="flex items-center"><span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span> Running Attack Phase...</span>
          ) : (
            <span className="flex items-center"><Play className="w-4 h-4 mr-2" /> Launch Fuzzer</span>
          )}
        </button>
      </div>
    </div>
  );
}