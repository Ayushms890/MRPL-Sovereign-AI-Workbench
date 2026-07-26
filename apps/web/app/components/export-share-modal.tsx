"use client";

import React, { useState } from "react";
import { Download, Share2, Copy, Check, X, FileText, Code } from "lucide-react";
import toast from "react-hot-toast";

import { useAuth } from "../contexts/auth-context";

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
  conversationId?: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function ExportShareModal({ isOpen, onClose, title, messages, conversationId }: ExportShareModalProps) {
  const { getToken } = useAuth();
  const [copiedShare, setCopiedShare] = useState(false);
  const [sharingUrl, setSharingUrl] = useState<string | null>(null);
  const [isGeneratingShare, setIsGeneratingShare] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  if (!isOpen) return null;

  const generateShareLink = async () => {
    if (!conversationId) {
      toast.error("No active conversation to share");
      return;
    }
    setIsGeneratingShare(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/conversations/${conversationId}/share`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!res.ok) {
        throw new Error("Failed to generate share snapshot");
      }
      const data = await res.json();
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      setSharingUrl(`${origin}/share/${data.share_id}`);
      toast.success("Shareable link generated!");
    } catch (err: any) {
      toast.error(err.message || "Failed to share conversation");
    } finally {
      setIsGeneratingShare(false);
    }
  };

  const copyShareLink = () => {
    if (sharingUrl) {
      navigator.clipboard.writeText(sharingUrl);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
      toast.success("Link copied to clipboard!");
    }
  };

  const revokeShareLink = async () => {
    if (!conversationId) return;
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/conversations/${conversationId}/share`, {
        method: "DELETE",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!res.ok) {
        throw new Error("Failed to revoke share link");
      }
      setSharingUrl(null);
      toast.success("Share link revoked successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to revoke share link");
    }
  };

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

          <button
            type="button"
            onClick={generateShareLink}
            disabled={isGeneratingShare}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 16px",
              background: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
              cursor: isGeneratingShare ? "not-allowed" : "pointer",
              textAlign: "left",
              color: "#334155",
              opacity: isGeneratingShare ? 0.7 : 1,
            }}
          >
            <Share2 size={20} style={{ color: "#818cf8" }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: "13px" }}>{isGeneratingShare ? "Generating Link..." : "Generate Shareable Link"}</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>Create a read-only public snapshot URL</div>
            </div>
          </button>

          {sharingUrl && (
            <div style={{ marginTop: 8, padding: 12, background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: 8 }}>
              <div style={{ fontSize: "11px", fontWeight: 600, color: "#64748b", marginBottom: 6 }}>Shareable link:</div>
              <div style={{ display: "flex", gap: 6 }}>
                <input
                  type="text"
                  readOnly
                  value={sharingUrl}
                  style={{
                    flex: 1,
                    padding: "6px 10px",
                    fontSize: "12px",
                    border: "1px solid #cbd5e1",
                    borderRadius: 6,
                    background: "#ffffff",
                    outline: "none",
                  }}
                  onClick={(e) => (e.target as HTMLInputElement).select()}
                />
                <button
                  type="button"
                  onClick={copyShareLink}
                  style={{
                    padding: "6px 12px",
                    background: "var(--accent, #6366f1)",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: 6,
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {copiedLink ? "Copied" : "Copy"}
                </button>
              </div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 8 }}>
                <span style={{ fontSize: "11px", color: "#e11d48", fontWeight: 500 }}>
                  ⚠️ Expires in 30 days
                </span>
                <button
                  type="button"
                  onClick={revokeShareLink}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#dc2626",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: "pointer",
                    textDecoration: "underline",
                    padding: 0,
                  }}
                >
                  Unshare link
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
