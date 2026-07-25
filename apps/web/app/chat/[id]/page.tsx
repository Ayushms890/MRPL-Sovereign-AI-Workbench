"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useChat } from "../../chat-context";
import { User, Bot, Wrench, Copy, ThumbsUp, ThumbsDown, Share2, PanelRightOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExecutionTrace } from "../../components/execution-trace";
import { MermaidDiagram } from "../../components/mermaid-diagram";
import { SpeechPlayer } from "../../components/voice-input";
import { ArtifactDrawer } from "../../components/artifact-drawer";
import { ExportShareModal } from "../../components/export-share-modal";
import { ChartRenderer } from "../../components/chart-renderer";

export default function ChatSessionPage() {
  const params = useParams();
  const chatId = params.id as string;

  const [artifact, setArtifact] = useState<{ title: string; language: string; content: string } | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const {
    token,
    messages,
    conversations,
    isSending,
    currentExecutionSteps,
    setActiveConversationId,
    loadMessages,
  } = useChat();

  const currentConv = conversations.find((c) => c.id === chatId);

  useEffect(() => {
    if (chatId && token) {
      setActiveConversationId(chatId);
      void loadMessages(token, chatId);
    }
  }, [chatId, token]);

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

  return (
    <div className="messages-container" style={{ display: "flex", width: "100%" }}>
      <div className="messages" style={{ flex: 1 }}>

        {messages.map((message) => {
          const isUser = message.role === "user";
          return (
            <div key={message.id} className={`message-group ${isUser ? "user-group" : "assistant-group"}`}>
              <div
                className={`message-avatar ${isUser ? "user-avatar" : "assistant-avatar"}`}
                style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </div>

              <div className="message-bubble-wrapper">
                {!isUser && message.execution_steps && message.execution_steps.length > 0 && (
                  <ExecutionTrace steps={message.execution_steps} isPending={false} />
                )}

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
                    <div className="tool-pill" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span className="tool-icon" style={{ display: "flex", alignItems: "center" }}>
                        <Wrench size={12} />
                      </span>
                      <span>Used Tool: <code>{message.tool_name}</code></span>
                    </div>
                  )}
                </article>

                {!isUser && (
                  <div className="message-actions">
                    <button
                      type="button"
                      className="action-btn"
                      title="Copy output"
                      onClick={() => navigator.clipboard.writeText(message.content)}
                      style={{ display: "flex", alignItems: "center", gap: 4 }}
                    >
                      <Copy size={12} />
                      <span>Copy</span>
                    </button>

                    <SpeechPlayer text={message.content} />

                    <button type="button" className="action-btn" title="Helpful" style={{ display: "flex", alignItems: "center" }}>
                      <ThumbsUp size={12} />
                    </button>
                    <button type="button" className="action-btn" title="Not helpful" style={{ display: "flex", alignItems: "center" }}>
                      <ThumbsDown size={12} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Live Job Execution Steps Trace */}
        {isSending && (
          <div className="message-group assistant-group pending-group">
            <div
              className="message-avatar assistant-avatar"
              style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              <Bot size={16} />
            </div>
            <div className="message-bubble-wrapper" style={{ width: "100%" }}>
              {currentExecutionSteps.length > 0 ? (
                <ExecutionTrace steps={currentExecutionSteps} isPending={true} />
              ) : (
                <article className="message-bubble pending-bubble">
                  <span>Archimedes</span>
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p className="pending-text">Planner is reasoning...</p>
                </article>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Artifact Drawer (Claude Split-Screen Canvas) */}
      <ArtifactDrawer
        isOpen={!!artifact}
        onClose={() => setArtifact(null)}
        title={artifact?.title || "Artifact"}
        language={artifact?.language || "text"}
        content={artifact?.content || ""}
      />

      {/* Export & Share Modal */}
      <ExportShareModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        title={currentConv?.title || "Archimedes Chat"}
        messages={messages}
      />
    </div>
  );
}
