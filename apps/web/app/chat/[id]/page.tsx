"use client";

import React, { useEffect } from "react";
import { useParams } from "next/navigation";
import { useChat } from "../../chat-context";
import { User, Bot, Wrench, Copy, ThumbsUp, ThumbsDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExecutionTrace } from "../../components/execution-trace";
import { StreamingThoughtAccordion } from "../../components/streaming-thought-accordion";

export default function ChatSessionPage() {
  const params = useParams();
  const chatId = params.id as string;

  const {
    token,
    messages,
    isSending,
    currentExecutionSteps,
    streamingThought,
    streamingDelta,
    streamingStatus,
    streamingTool,
    streamingAgent,
    isStreamingActive,
    setActiveConversationId,
    loadMessages,
  } = useChat();

  useEffect(() => {
    if (chatId && token) {
      setActiveConversationId(chatId);
      void loadMessages(token, chatId);
    }
  }, [chatId, token]);

  return (
    <div className="messages">
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
                <div className="message-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
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

      {/* Live SSE Streaming Thought & Token Response */}
      {isStreamingActive && (
        <div className="message-group assistant-group pending-group">
          <div
            className="message-avatar assistant-avatar"
            style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            <Bot size={16} />
          </div>
          <div className="message-bubble-wrapper" style={{ width: "100%" }}>
            <StreamingThoughtAccordion
              thoughtText={streamingThought}
              isThinking={!streamingDelta}
              statusText={streamingStatus}
              toolName={streamingTool}
              agentName={streamingAgent}
              isStreamingDone={!isStreamingActive}
            />

            {streamingDelta ? (
              <article className="message-bubble">
                <span>Archimedes</span>
                <div className="message-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingDelta}
                  </ReactMarkdown>
                </div>
              </article>
            ) : (
              !streamingThought && (
                <article className="message-bubble pending-bubble">
                  <span>Archimedes</span>
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p className="pending-text">{streamingStatus || "Planner is reasoning..."}</p>
                </article>
              )
            )}
          </div>
        </div>
      )}

      {/* Background Job Trace Fallback (if non-streaming job active) */}
      {isSending && !isStreamingActive && (
        <div className="message-group assistant-group pending-group">
          <div
            className="message-avatar assistant-avatar"
            style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            <Bot size={16} />
          </div>
          <div className="message-bubble-wrapper">
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
                <p className="pending-text">Planner is executing workflow...</p>
              </article>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
