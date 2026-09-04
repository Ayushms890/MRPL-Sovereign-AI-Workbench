"use client";

import React, { useRef, useState } from "react";
import { FileText, Upload, X, Trash2, Loader2, File as FileIcon } from "lucide-react";
import toast from "react-hot-toast";
import { useChat } from "../chat-context";

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentUploadModal({ isOpen, onClose }: DocumentUploadModalProps) {
  const {
    documents,
    documentTitle,
    setDocumentTitle,
    documentContent,
    setDocumentContent,
    documentStatus,
    isUploadingDocument,
    uploadDocument,
    deleteDocument,
  } = useChat();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFilePick = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".txt") && file.type !== "text/plain") {
      toast.error("Only .txt files can be read directly — paste other formats as text below.");
      return;
    }

    try {
      const text = await file.text();
      setFileName(file.name);
      if (!documentTitle.trim()) {
        setDocumentTitle(file.name.replace(/\.txt$/i, ""));
      }
      setDocumentContent(text);
      toast.success(`Loaded ${file.name}`);
    } catch (err) {
      toast.error("Could not read that file");
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    await uploadDocument(event);
    setFileName(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
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
      onClick={onClose}
    >
      <div
        style={{
          width: "480px",
          maxHeight: "85vh",
          overflowY: "auto",
          background: "#ffffff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <header
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#f8fafc",
            position: "sticky",
            top: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Upload size={18} style={{ color: "#4f46e5" }} />
            <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 600, color: "#1e293b" }}>
              Upload Knowledge Document
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#64748b" }}
          >
            <X size={18} />
          </button>
        </header>

        <form onSubmit={handleSubmit} style={{ padding: "20px", display: "flex", flexDirection: "column", gap: 14 }}>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "12px 16px",
              background: "#f8fafc",
              border: "1px dashed #94a3b8",
              borderRadius: "8px",
              cursor: "pointer",
              textAlign: "left",
              color: "#334155",
            }}
          >
            <FileIcon size={18} style={{ color: "#4f46e5" }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: "13px" }}>
                {fileName ? fileName : "Choose a .txt file"}
              </div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>
                Or paste the report content directly below
              </div>
            </div>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,text/plain"
            onChange={handleFilePick}
            style={{ display: "none" }}
          />

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: "12px", fontWeight: 600, color: "#475569" }}>Title</label>
            <input
              type="text"
              value={documentTitle}
              onChange={(e) => setDocumentTitle(e.target.value)}
              placeholder="e.g. DHDT Shift Report 2026-09-04"
              style={{
                padding: "9px 12px",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                fontSize: "13px",
                color: "#0f172a",
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: "12px", fontWeight: 600, color: "#475569" }}>Content</label>
            <textarea
              value={documentContent}
              onChange={(e) => setDocumentContent(e.target.value)}
              placeholder="Paste the shift report, SOP, or guidance text here..."
              rows={10}
              style={{
                padding: "9px 12px",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                fontSize: "13px",
                color: "#0f172a",
                fontFamily: "inherit",
                resize: "vertical",
              }}
            />
          </div>

          {documentStatus && (
            <div style={{ fontSize: "12px", color: "#64748b" }}>{documentStatus}</div>
          )}

          <button
            type="submit"
            disabled={isUploadingDocument}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              padding: "10px 16px",
              background: isUploadingDocument ? "#a5b4fc" : "#4f46e5",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              cursor: isUploadingDocument ? "default" : "pointer",
              fontWeight: 600,
              fontSize: "13px",
            }}
          >
            {isUploadingDocument ? <Loader2 size={16} className="spin" /> : <Upload size={16} />}
            {isUploadingDocument ? "Embedding..." : "Upload to Knowledge Base"}
          </button>

          {documents.length > 0 && (
            <div style={{ marginTop: 8, borderTop: "1px solid #e2e8f0", paddingTop: 12 }}>
              <div style={{ fontSize: "12px", fontWeight: 600, color: "#475569", marginBottom: 8 }}>
                Uploaded documents ({documents.length})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 10px",
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
                      borderRadius: "6px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                      <FileText size={14} style={{ color: "#4f46e5", flexShrink: 0 }} />
                      <span
                        style={{
                          fontSize: "12px",
                          color: "#334155",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={doc.title}
                      >
                        {doc.title}
                      </span>
                      <span style={{ fontSize: "11px", color: "#94a3b8", flexShrink: 0 }}>
                        {doc.chunk_count} chunks
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => deleteDocument(doc.id)}
                      style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8" }}
                      title="Delete document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
