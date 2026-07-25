"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Cpu, Wrench, CheckCircle2, Loader2, AlertCircle, Lightbulb } from "lucide-react";

export type ExecutionStep = {
  step: string;
  label: string;
  status: string;
  timestamp: string;
  metadata?: Record<string, any>;
};

interface ExecutionTraceProps {
  steps: ExecutionStep[];
  isPending?: boolean;
}

export function ExecutionTrace({ steps, isPending = false }: ExecutionTraceProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(isPending);
  const [openThoughts, setOpenThoughts] = useState<Record<number, boolean>>({});

  if (!steps || steps.length === 0) return null;

  const toggleThought = (idx: number) => {
    setOpenThoughts((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="execution-trace-card" style={{ margin: "10px 0", borderRadius: 8, border: "2px solid #000000", background: "#f8fafc", overflow: "hidden", fontSize: "13px" }}>
      {/* Header Bar */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: "100%",
          padding: "8px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#0f172a",
          color: "#ffffff",
          border: "none",
          cursor: "pointer",
          fontWeight: 600,
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Cpu size={14} style={{ color: "#38bdf8" }} />
          <span>Workflow Trace ({steps.length} {steps.length === 1 ? "step" : "steps"})</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isPending && <span style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 500 }}>Live Running...</span>}
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Step List Body */}
      {isExpanded && (
        <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "8px", background: "#ffffff" }}>
          {steps.map((item, idx) => {
            const isCompleted = item.status === "completed";
            const isFailed = item.status === "failed";
            const isRunning = item.status === "running";
            const isThoughtOpen = !!openThoughts[idx];

            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 10,
                  padding: "6px 8px",
                  borderRadius: 6,
                  background: isRunning ? "#f0f9ff" : isFailed ? "#fef2f2" : "#f8fafc",
                  border: isRunning ? "1px solid #bae6fd" : "1px solid #e2e8f0",
                }}
              >
                <div style={{ marginTop: 2, flexShrink: 0 }}>
                  {isCompleted && <CheckCircle2 size={14} style={{ color: "#16a34a" }} />}
                  {isFailed && <AlertCircle size={14} style={{ color: "#dc2626" }} />}
                  {isRunning && <Loader2 size={14} className="animate-spin" style={{ color: "#0284c7" }} />}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: "#1e293b" }}>{item.label}</div>
                  
                  {item.metadata && item.metadata.tool_name && (
                    <div style={{ marginTop: 4, display: "flex", alignItems: "center", gap: 6, fontSize: "11px", color: "#475569" }}>
                      <Wrench size={11} />
                      <span>Tool: <code>{item.metadata.tool_name}</code></span>
                    </div>
                  )}

                  {item.metadata && item.metadata.thought && (
                    <div style={{ marginTop: 6 }}>
                      <button
                        type="button"
                        onClick={() => toggleThought(idx)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          background: "#f1f5f9",
                          border: "1px solid #cbd5e1",
                          borderRadius: 4,
                          padding: "4px 8px",
                          fontSize: "11px",
                          color: "#334155",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        <Lightbulb size={12} style={{ color: "#eab308" }} />
                        <span>View Model Reasoning</span>
                        {isThoughtOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>
                      {isThoughtOpen && (
                        <div style={{ marginTop: 6, padding: 8, background: "#f8fafc", borderLeft: "3px solid #eab308", borderRadius: 4, fontFamily: "monospace", fontSize: "11px", whiteSpace: "pre-wrap", color: "#475569" }}>
                          {item.metadata.thought}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", flexShrink: 0 }}>
                  {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
