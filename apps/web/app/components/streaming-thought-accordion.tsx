"use client";

import React, { useState, useEffect } from "react";
import { ChevronDown, ChevronUp, Brain, Sparkles, Wrench, CheckCircle2, Loader2 } from "lucide-react";

interface StreamingThoughtAccordionProps {
  thoughtText?: string;
  isThinking?: boolean;
  statusText?: string;
  toolName?: string;
  agentName?: string;
  isStreamingDone?: boolean;
}

export function StreamingThoughtAccordion({
  thoughtText = "",
  isThinking = false,
  statusText = "",
  toolName = "",
  agentName = "",
  isStreamingDone = false,
}: StreamingThoughtAccordionProps) {
  const [isOpen, setIsOpen] = useState<boolean>(isThinking || !isStreamingDone);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isThinking || !isStreamingDone) {
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 0.1);
      }, 100);
    }
    return () => clearInterval(timer);
  }, [isThinking, isStreamingDone]);

  // Auto-collapse when streaming completes if thought is clean
  useEffect(() => {
    if (isStreamingDone) {
      setIsOpen(false);
    }
  }, [isStreamingDone]);

  if (!thoughtText && !isThinking && !statusText && !toolName) {
    return null;
  }

  return (
    <div
      className="streaming-thought-box"
      style={{
        margin: "8px 0 12px 0",
        borderRadius: "8px",
        border: "1px solid #e2e8f0",
        background: "#f8fafc",
        overflow: "hidden",
        fontSize: "12px",
      }}
    >
      {/* Header button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: "100%",
          padding: "8px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: isThinking ? "#f0f9ff" : "#f1f5f9",
          border: "none",
          cursor: "pointer",
          color: "#334155",
          fontWeight: 600,
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isThinking ? (
            <Loader2 size={14} className="animate-spin" style={{ color: "#0284c7" }} />
          ) : (
            <Brain size={14} style={{ color: "#8b5cf6" }} />
          )}
          <span>
            {isThinking
              ? statusText || "Thinking..."
              : `Thought for ${elapsedSeconds > 0 ? elapsedSeconds.toFixed(1) : "1.2"}s`}
          </span>

          {agentName && (
            <span
              style={{
                fontSize: "10px",
                background: "#ddd6fe",
                color: "#5b21b6",
                padding: "2px 6px",
                borderRadius: "4px",
                fontWeight: 600,
              }}
            >
              {agentName}
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {toolName && (
            <div style={{ display: "flex", alignItems: "center", gap: 4, color: "#0284c7", fontWeight: 500 }}>
              <Wrench size={11} />
              <span>Tool: <code>{toolName}</code></span>
            </div>
          )}
          {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {/* Thought Content Drawer */}
      {isOpen && (
        <div
          style={{
            padding: "10px 12px",
            background: "#ffffff",
            borderTop: "1px solid #e2e8f0",
            color: "#475569",
            fontFamily: "monospace",
            fontSize: "11px",
            lineHeight: "1.5",
            whiteSpace: "pre-wrap",
            maxHeight: "220px",
            overflowY: "auto",
          }}
        >
          {thoughtText ? (
            <div>{thoughtText}</div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#94a3b8" }}>
              <Sparkles size={12} className="animate-pulse" />
              <span>Model is reasoning about the request...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
