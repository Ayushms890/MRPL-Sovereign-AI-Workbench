"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

interface ChartSpec {
  chart_type: "bar" | "line" | "pie" | "area";
  title: string;
  data: Record<string, any>[];
  x_key: string;
  y_keys: string[];
}

const COLORS = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"];

export function ChartRenderer({ jsonContent }: { jsonContent: string }) {
  try {
    const spec: ChartSpec = JSON.parse(jsonContent);
    const { chart_type = "bar", title = "Chart", data = [], x_key = "", y_keys = [] } = spec;

    if (!data || data.length === 0) {
      return (
        <div style={{ padding: "12px", background: "#f8fafc", borderRadius: "6px", color: "#64748b", fontSize: "12px" }}>
          No chart data points available.
        </div>
      );
    }

    return (
      <div
        className="chart-container shadow-sm"
        style={{
          margin: "16px 0",
          padding: "20px",
          background: "#ffffff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          width: "100%",
        }}
      >
        <h4 style={{ margin: "0 0 16px 0", fontSize: "15px", fontWeight: 600, color: "#1e293b", textAlign: "center" }}>
          {title}
        </h4>

        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            {chart_type === "line" ? (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey={x_key} stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: "#0f172a", color: "#ffffff", borderRadius: "8px", border: "none" }} />
                <Legend />
                {y_keys.map((key, idx) => (
                  <Line key={key} type="monotone" dataKey={key} stroke={COLORS[idx % COLORS.length]} strokeWidth={3} dot={{ r: 4 }} />
                ))}
              </LineChart>
            ) : chart_type === "area" ? (
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey={x_key} stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: "#0f172a", color: "#ffffff", borderRadius: "8px", border: "none" }} />
                <Legend />
                {y_keys.map((key, idx) => (
                  <Area key={key} type="monotone" dataKey={key} fill={COLORS[idx % COLORS.length]} stroke={COLORS[idx % COLORS.length]} fillOpacity={0.4} />
                ))}
              </AreaChart>
            ) : chart_type === "pie" ? (
              <PieChart>
                <Tooltip contentStyle={{ background: "#0f172a", color: "#ffffff", borderRadius: "8px", border: "none" }} />
                <Legend />
                <Pie data={data} dataKey={y_keys[0] || "value"} nameKey={x_key} cx="50%" cy="50%" outerRadius={100} label>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            ) : (
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey={x_key} stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: "#0f172a", color: "#ffffff", borderRadius: "8px", border: "none" }} />
                <Legend />
                {y_keys.map((key, idx) => (
                  <Bar key={key} dataKey={key} fill={COLORS[idx % COLORS.length]} radius={[6, 6, 0, 0]} />
                ))}
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>
    );
  } catch (err) {
    console.error("Failed to render chart spec:", err);
    return (
      <div style={{ padding: "12px", background: "#fef2f2", color: "#991b1b", borderRadius: "6px", fontSize: "12px" }}>
        <code>{jsonContent}</code>
      </div>
    );
  }
}
