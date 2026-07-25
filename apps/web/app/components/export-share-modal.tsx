"use client";

import React, { useState } from "react";
import { Download, Share2, Copy, Check, X, FileText, Code } from "lucide-react";
import toast from "react-hot-toast";

interface Message {
  id: string;
  role: string;
  content: string;
  tool_name?: string | null;
  created_at: string;
}

interface ExportShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  messages: Message[];
}

export function ExportShareModal({ isOpen, onClose, title, messages }: ExportShareModalProps) {
  const [copiedShare, setCopiedShare] = useState(false);

  if (!isOpen) return null;

  const exportMarkdown = () => {
    const md = messages
      .map((m) => `### ${m.role === "user" ? "User" : "Archimedes"}\n${m.content}\n`)
      .join("\n---\n\n");
    const blob = new Blob([`# ${title}\n\n${md}`], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, "_")}_export.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Exported Markdown file!");
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify({ title, messages }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, "_")}_export.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Exported JSON file!");
  };

  const copyShareSummary = () => {
    const summary = `Session: ${title}\nMessages: ${messages.length}\nArchimedes AI OS Session`;
    navigator.clipboard.writeText(summary);
    setCopiedShare(true);
    setTimeout(() => setCopiedShare(false), 2000);
    toast.success("Session summary copied!");
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(15, 23, 42, 0.5)",
        backdropFilter: "blur(4px)",
        zIndex: 999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: "420px",
          background: "#ffffff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
          overflow: "hidden",
        }}
      >
        <header
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#f8fafc",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Share2 size={18} style={{ color: "#4f46e5" }} />
            <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 600, color: "#1e293b" }}>Export & Share Session</h3>
          </div>
          <button type="button" onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#64748b" }}>
            <X size={18} />
          </button>
        </header>

        <div style={{ padding: "20px", display: "flex", flexDirection: "column", gap: 12 }}>
          <button
            type="button"
            onClick={exportMarkdown}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 16px",
              background: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
              cursor: "pointer",
              textAlign: "left",
              color: "#334155",
            }}
          >
            <FileText size={20} style={{ color: "#0284c7" }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: "13px" }}>Export as Markdown (.md)</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>Clean document format with headings & code blocks</div>
            </div>
          </button>

          <button
            type="button"
            onClick={exportJSON}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 16px",
              background: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
              cursor: "pointer",
              textAlign: "left",
              color: "#334155",
            }}
          >
            <Code size={20} style={{ color: "#16a34a" }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: "13px" }}>Export as Raw JSON (.json)</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>Full structured conversation payload</div>
            </div>
          </button>

          <button
            type="button"
            onClick={copyShareSummary}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 16px",
              background: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
              cursor: "pointer",
              textAlign: "left",
              color: "#334155",
            }}
          >
            {copiedShare ? <Check size={20} style={{ color: "#16a34a" }} /> : <Copy size={20} style={{ color: "#8b5cf6" }} />}
            <div>
              <div style={{ fontWeight: 600, fontSize: "13px" }}>Copy Session Summary</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>Copy formatted summary to clipboard</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
