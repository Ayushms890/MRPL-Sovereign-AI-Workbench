"use client";

import React, { useState } from "react";
import { X, Copy, Check, ExternalLink, Code2, Eye } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ArtifactDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  language?: string;
  content: string;
}

export function ArtifactDrawer({
  isOpen,
  onClose,
  title,
  language = "text",
  content,
}: ArtifactDrawerProps) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"preview" | "code">("code");

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside
      className="artifact-drawer shadow-2xl"
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: "550px",
        height: "100vh",
        background: "#ffffff",
        borderLeft: "1px solid #e2e8f0",
        zIndex: 99,
        display: "flex",
        flexDirection: "column",
        transition: "transform 0.3s ease-in-out",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "14px 18px",
          borderBottom: "1px solid #e2e8f0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#f8fafc",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Code2 size={18} style={{ color: "#4f46e5" }} />
          <div>
            <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 600, color: "#1e293b" }}>{title}</h3>
            <span style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>{language}</span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            type="button"
            onClick={handleCopy}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "6px 10px",
              background: "#ffffff",
              border: "1px solid #cbd5e1",
              borderRadius: "6px",
              fontSize: "12px",
              cursor: "pointer",
              color: "#334155",
            }}
          >
            {copied ? <Check size={14} style={{ color: "#16a34a" }} /> : <Copy size={14} />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: "6px",
              color: "#64748b",
            }}
          >
            <X size={18} />
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", background: "#f1f5f9", padding: "4px 8px" }}>
        <button
          type="button"
          onClick={() => setActiveTab("code")}
          style={{
            padding: "6px 12px",
            border: "none",
            background: activeTab === "code" ? "#ffffff" : "transparent",
            borderRadius: "4px",
            fontWeight: activeTab === "code" ? 600 : 400,
            fontSize: "12px",
            cursor: "pointer",
            color: activeTab === "code" ? "#1e293b" : "#64748b",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Code2 size={13} />
          Code
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("preview")}
          style={{
            padding: "6px 12px",
            border: "none",
            background: activeTab === "preview" ? "#ffffff" : "transparent",
            borderRadius: "4px",
            fontWeight: activeTab === "preview" ? 600 : 400,
            fontSize: "12px",
            cursor: "pointer",
            color: activeTab === "preview" ? "#1e293b" : "#64748b",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Eye size={13} />
          Preview
        </button>
      </div>

      {/* Body Content */}
      <div style={{ flex: 1, padding: "16px", overflowY: "auto", background: activeTab === "code" ? "#0f172a" : "#ffffff" }}>
        {activeTab === "code" ? (
          <pre style={{ margin: 0, fontFamily: "monospace", fontSize: "12px", color: "#f8fafc", lineHeight: "1.6" }}>
            <code>{content}</code>
          </pre>
        ) : (
          <div className="artifact-markdown" style={{ fontSize: "14px", lineHeight: "1.6", color: "#334155" }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </aside>
  );
}
