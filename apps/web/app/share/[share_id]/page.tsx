"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../contexts/auth-context";
import { Bot, User, Wrench, Download, LogIn, PlusCircle, Share2, PanelRightOpen, ArrowLeft, AlertTriangle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MermaidDiagram } from "../../components/mermaid-diagram";
import { ChartRenderer } from "../../components/chart-renderer";
import { ArtifactDrawer } from "../../components/artifact-drawer";
import toast from "react-hot-toast";

interface Message {
  id: string;
  role: string;
  content: string;
  tool_name: string | null;
  tool_output?: string | null;
  created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SharedChatPage() {
  const params = useParams();
  const router = useRouter();
  const shareId = params.share_id as string;
  const { isLoaded, isSignedIn, getToken } = useAuth();

  const [title, setTitle] = useState<string>("Shared Chat");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [artifact, setArtifact] = useState<{ title: string; language: string; content: string } | null>(null);

  // 1. Redirect to login if not authenticated
  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.replace(`/auth?redirect=/share/${shareId}`);
    }
  }, [isLoaded, isSignedIn, shareId, router]);

  // 2. Fetch shared snapshot
  useEffect(() => {
    const fetchSharedChat = async () => {
      if (!shareId) return;
      try {
        const res = await fetch(`${API_URL}/conversations/share/${shareId}`);
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error("Shared chat snapshot not found or has expired");
          }
          throw new Error("Failed to load shared conversation");
        }
        const data = await res.json();
        setTitle(data.title);
        setMessages(data.messages || []);
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred");
      } finally {
        setIsLoading(false);
      }
    };

    if (isSignedIn) {
      void fetchSharedChat();
    }
  }, [shareId, isSignedIn]);

  // 3. Import chat to user's workspace
  const handleImport = async () => {
    setIsImporting(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/conversations/share/${shareId}/import`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!res.ok) {
        throw new Error("Failed to import conversation to workspace");
      }

      const newConv = await res.json();
      toast.success("Conversation successfully added to your workspace!");
      router.push(`/chat/${newConv.id}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to import chat");
    } finally {
      setIsImporting(false);
    }
  };

  const renderMarkdownComponents = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || "");
      const lang = match ? match[1] : "";
      const codeString = String(children).replace(/\n$/, "");

      if (!inline && lang === "mermaid") {
        return <MermaidDiagram chart={codeString} />;
      }

      if (!inline && (lang === "chart" || className?.includes("json:chart") || codeString.includes('"chart_type":'))) {
        return <ChartRenderer jsonContent={codeString} />;
      }

      if (!inline && codeString.length > 80) {
        return (
          <div style={{ position: "relative" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#1e293b", color: "#94a3b8", padding: "4px 12px", borderRadius: "6px 6px 0 0", fontSize: "11px" }}>
              <span>{lang || "code"}</span>
              <button
                type="button"
                onClick={() => setArtifact({ title: "Code Snippet", language: lang || "code", content: codeString })}
                style={{ background: "none", border: "none", color: "#38bdf8", cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}
              >
                <PanelRightOpen size={12} />
                <span>Open Canvas</span>
              </button>
            </div>
            <pre className={className} {...props} style={{ marginTop: 0, borderRadius: "0 0 6px 6px" }}>
              <code>{children}</code>
            </pre>
          </div>
        );
      }

      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
  };

  if (!isLoaded || isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "var(--background)", color: "var(--text-muted)", fontSize: "14px" }}>
        Loading shared conversation...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", gap: 16 }}>
        <AlertTriangle size={48} style={{ color: "#ef4444" }} />
        <h2 style={{ fontSize: "18px", fontWeight: 600 }}>Error Loading Shared Chat</h2>
        <p style={{ color: "#64748b", fontSize: "14px" }}>{error}</p>
        <button
          type="button"
          onClick={() => router.push("/chat")}
          style={{ padding: "8px 16px", background: "var(--accent, #6366f1)", color: "#ffffff", border: "none", borderRadius: 8, fontSize: "14px", fontWeight: 600, cursor: "pointer" }}
        >
          Go to Workspace
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", width: "100vw", overflow: "hidden", background: "var(--background)" }}>
      {/* Top Banner Navigation */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 24px",
          borderBottom: "1px solid #cbd5e1",
          background: "#ffffff",
          height: "56px",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            type="button"
            onClick={() => router.push("/chat")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#64748b",
              fontSize: "13px",
              fontWeight: 500,
            }}
          >
            <ArrowLeft size={16} />
            <span>Workspace</span>
          </button>
          <span style={{ height: "16px", width: "1px", background: "#cbd5e1" }}></span>
          <h2 style={{ fontSize: "15px", fontWeight: 600, color: "#1e293b", margin: 0 }}>{title}</h2>
          <span
            style={{
              fontSize: "10px",
              fontWeight: 600,
              color: "#4f46e5",
              background: "#e0e7ff",
              padding: "2px 8px",
              borderRadius: "12px",
            }}
          >
            Shared Read-Only
          </span>
        </div>

        <div>
          <button
            type="button"
            onClick={handleImport}
            disabled={isImporting}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "8px 16px",
              background: "var(--accent, #6366f1)",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: isImporting ? "not-allowed" : "pointer",
              opacity: isImporting ? 0.8 : 1,
            }}
          >
            <PlusCircle size={16} />
            <span>{isImporting ? "Adding to Workspace..." : "Add to My Workspace"}</span>
          </button>
        </div>
      </header>

      {/* Message Feed */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 0" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto", padding: "0 24px", display: "flex", flexDirection: "column", gap: 24 }}>
          {messages.map((message) => {
            const isUser = message.role === "user";
            return (
              <div key={message.id} className={`message-group ${isUser ? "user-group" : "assistant-group"}`}>
                <div
                  className={`message-avatar ${isUser ? "user-avatar" : "assistant-avatar"}`}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}
                >
                  {isUser ? <User size={16} /> : <Bot size={16} />}
                </div>

                <div className="message-bubble-wrapper" style={{ flex: 1 }}>
                  <article className="message-bubble">
                    <span>{isUser ? "You" : "Archimedes"}</span>
                    
                    {!isUser && message.tool_name === "chart_generator" && message.tool_output && !message.content.includes('"chart_type"') && (
                      <ChartRenderer jsonContent={message.tool_output} />
                    )}

                    <div className="message-markdown">
                      <ReactMarkdown remarkPlugins={[remarkGfm]} components={renderMarkdownComponents}>
                        {message.content}
                      </ReactMarkdown>
                    </div>

                    {message.tool_name && (
                      <div className="tool-pill" style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 12 }}>
                        <span className="tool-icon" style={{ display: "flex", alignItems: "center" }}>
                          <Wrench size={12} />
                        </span>
                        <span>Used Tool: <code>{message.tool_name}</code></span>
                      </div>
                    )}
                  </article>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <ArtifactDrawer
        isOpen={!!artifact}
        onClose={() => setArtifact(null)}
        title={artifact?.title || "Artifact"}
        language={artifact?.language || "text"}
        content={artifact?.content || ""}
      />
    </div>
  );
}
