"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  FormEvent,
  useMemo,
} from "react";
import { useRouter } from "next/navigation";
import { createApiClient } from "../lib/api-client";
import { useAuth } from "./auth-context";
import { useUi } from "./ui-context";
import { useApiKeys } from "./api-keys-context";
import toast from "react-hot-toast";

export type Conversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ExecutionStep = {
  step: string;
  label: string;
  status: string;
  timestamp: string;
  metadata?: Record<string, any>;
};

export type Message = {
  id: string;
  role: string;
  content: string;
  tool_name: string | null;
  created_at: string;
  execution_steps?: ExecutionStep[];
};

export type SuggestionCard = {
  title: string;
  desc: string;
  prompt: string;
};

export const suggestionCards: SuggestionCard[] = [
  {
    title: "Write design specs",
    desc: "Draft a system integration document",
    prompt:
      "Write a high-level system integration design specification for connecting FastAPI with next.js via REST, including error boundaries.",
  },
  {
    title: "Audit database indexes",
    desc: "Recommend indexing strategies for pgvector",
    prompt:
      "Provide an optimal indexing strategy for pgvector HNSW index configurations on high dimension vector models (e.g. 768 dimensions).",
  },
  {
    title: "Optimize API routes",
    desc: "Analyze dependencies and middleware latency",
    prompt:
      "Show how to structure modular FastAPI dependencies to reuse database connections, leverage NullPool correctly, and reduce connection overhead.",
  },
  {
    title: "Draft release notes",
    desc: "Summarize brutalist design system updates",
    prompt:
      "Draft comprehensive release notes explaining the resizable/collapsible retro-brutalist sidebar features, dynamic routes, and SVG icons.",
  },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ConversationContextType = {
  conversations: Conversation[];
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>;
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  currentExecutionSteps: ExecutionStep[];
  editingConversationId: string | null;
  setEditingConversationId: (id: string | null) => void;
  editingTitle: string;
  setEditingTitle: (title: string) => void;
  conversationGroups: [string, Conversation[]][];
  streamingThought: string;
  streamingDelta: string;
  streamingStatus: string;
  streamingTool: string;
  streamingAgent: string;
  isStreamingActive: boolean;
  loadConversations: (authToken?: string) => Promise<void>;
  loadMessages: (authToken: string | undefined, conversationId: string) => Promise<void>;
  createConversation: () => Promise<Conversation | null>;
  deleteConversation: (conversationId: string) => Promise<void>;
  renameConversation: (conversationId: string, newTitle: string) => Promise<void>;
  sendMessage: (
    event?: FormEvent<HTMLFormElement>,
    textOverride?: string,
    conversationIdOverride?: string
  ) => Promise<void>;
};

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export const ConversationProvider = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter();
  const { getToken, isAuthenticated } = useAuth();
  const { setStatus, setIsSending, setDraft, draft, setIsApiKeyWarningOpen } = useUi();
  const { configuredProviders } = useApiKeys();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentExecutionSteps, setCurrentExecutionSteps] = useState<ExecutionStep[]>([]);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  // Live SSE Streaming States
  const [streamingThought, setStreamingThought] = useState("");
  const [streamingDelta, setStreamingDelta] = useState("");
  const [streamingStatus, setStreamingStatus] = useState("");
  const [streamingTool, setStreamingTool] = useState("");
  const [streamingAgent, setStreamingAgent] = useState("");
  const [isStreamingActive, setIsStreamingActive] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      void loadConversations();
    }
  }, [isAuthenticated]);

  const conversationGroups = useMemo(() => {
    const today: Conversation[] = [];
    const yesterday: Conversation[] = [];
    const older: Conversation[] = [];

    const now = new Date();
    const oneDay = 24 * 60 * 60 * 1000;

    conversations.forEach((conv) => {
      const convDate = new Date(conv.created_at);
      const diffDays = Math.floor((now.getTime() - convDate.getTime()) / oneDay);

      if (diffDays === 0) {
        today.push(conv);
      } else if (diffDays === 1) {
        yesterday.push(conv);
      } else {
        older.push(conv);
      }
    });

    const groups: [string, Conversation[]][] = [];
    if (today.length > 0) groups.push(["Today", today]);
    if (yesterday.length > 0) groups.push(["Yesterday", yesterday]);
    if (older.length > 0) groups.push(["Older", older]);

    return groups;
  }, [conversations]);

  const api = useMemo(() => createApiClient(getToken), [getToken]);

  const loadConversations = async (authToken?: string) => {
    try {
      let data: Conversation[];
      if (authToken) {
        const response = await fetch(`${API_URL}/conversations`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (!response.ok) throw new Error("Failed to load conversations");
        data = await response.json();
      } else {
        data = await api<Conversation[]>("/conversations");
      }
      setConversations(data);
    } catch (error) {
      console.error("Error loading conversations:", error);
    }
  };

  const loadMessages = async (authToken: string | undefined, conversationId: string) => {
    try {
      let data: Message[];
      if (authToken) {
        const response = await fetch(
          `${API_URL}/conversations/${conversationId}/messages`,
          {
            headers: { Authorization: `Bearer ${authToken}` },
          }
        );
        if (!response.ok) throw new Error("Failed to load messages");
        data = await response.json();
      } else {
        data = await api<Message[]>(`/conversations/${conversationId}/messages`);
      }
      setMessages(data);
    } catch (error) {
      console.error("Error loading messages:", error);
    }
  };

  const createConversation = async (): Promise<Conversation | null> => {
    try {
      const newConv = await api<Conversation>("/conversations", {
        method: "POST",
        body: JSON.stringify({ title: "New Session" }),
      });
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
      router.push(`/chat/${newConv.id}`);
      return newConv;
    } catch (error) {
      console.error("Error creating conversation:", error);
      toast.error("Failed to create new conversation");
      return null;
    }
  };

  const deleteConversation = async (conversationId: string) => {
    try {
      await api(`/conversations/${conversationId}`, { method: "DELETE" });
      setConversations((prev) => prev.filter((c) => c.id !== conversationId));
      if (activeConversationId === conversationId) {
        setActiveConversationId(null);
        setMessages([]);
        router.push("/chat");
      }
      toast.success("Conversation deleted");
    } catch (error) {
      console.error("Error deleting conversation:", error);
      toast.error("Failed to delete conversation");
    }
  };

  const renameConversation = async (conversationId: string, newTitle: string) => {
    try {
      const updated = await api<Conversation>(`/conversations/${conversationId}`, {
        method: "PUT",
        body: JSON.stringify({ title: newTitle }),
      });
      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? updated : c))
      );
      toast.success("Renamed conversation");
    } catch (error) {
      console.error("Error renaming conversation:", error);
      toast.error("Failed to rename conversation");
    }
  };

  const sendMessage = async (
    event?: FormEvent<HTMLFormElement>,
    textOverride?: string,
    conversationIdOverride?: string
  ) => {
    if (event) event.preventDefault();

    if (configuredProviders.length === 0) {
      setIsApiKeyWarningOpen(true);
      return;
    }

    const content = textOverride ?? draft;
    if (!content.trim()) return;

    let targetId = conversationIdOverride ?? activeConversationId;
    if (!targetId) {
      const newConv = await createConversation();
      if (!newConv) return;
      targetId = newConv.id;
    }

    setDraft("");
    setIsSending(true);
    setStatus("Thinking...");

    try {
      const token = await getToken();

      const currentConv = conversations.find((c) => c.id === targetId);
      if (
        currentConv &&
        (currentConv.title.toLowerCase().startsWith("new session") ||
          currentConv.title.toLowerCase().startsWith("new chat") ||
          messages.length === 0)
      ) {
        const autoTitle = content.trim().slice(0, 30) + (content.trim().length > 30 ? "..." : "");
        void renameConversation(targetId, autoTitle);
      }

      // Add optimistic user message
      const userMsgId = `user-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: userMsgId,
          role: "user",
          content: content.trim(),
          tool_name: null,
          created_at: new Date().toISOString(),
        },
      ]);

      // Connect to SSE stream
      const response = await fetch(`${API_URL}/conversations/${targetId}/messages/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content: content.trim() }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Streaming failed with status ${response.status}`);
      }

      setIsStreamingActive(true);
      setStreamingThought("");
      setStreamingDelta("");
      setStreamingStatus("Planner analyzing prompt...");
      setStreamingTool("");
      setStreamingAgent("");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let currentEvent = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("event: ")) {
            currentEvent = trimmed.slice(7).trim();
          } else if (trimmed.startsWith("data: ")) {
            try {
              const data = JSON.parse(trimmed.slice(6));
              if (currentEvent === "thinking") {
                setStreamingStatus(data.status ?? "Thinking...");
              } else if (currentEvent === "thought") {
                setStreamingThought(data.thought ?? "");
              } else if (currentEvent === "agent_route") {
                setStreamingAgent(data.agent_name ?? "");
              } else if (currentEvent === "tool_start") {
                setStreamingTool(data.tool_name ?? "");
              } else if (currentEvent === "token") {
                setStreamingDelta((prev) => prev + (data.delta ?? ""));
              } else if (currentEvent === "done") {
                setMessages((current) => [
                  ...current.filter((m) => m.id !== userMsgId),
                  {
                    id: `user-${Date.now()}`,
                    role: "user",
                    content: content.trim(),
                    tool_name: null,
                    created_at: new Date().toISOString(),
                  },
                  {
                    id: data.message_id,
                    role: data.role ?? "assistant",
                    content: data.content,
                    tool_name: data.tool_name ?? null,
                    created_at: new Date().toISOString(),
                  },
                ]);
                setIsStreamingActive(false);
                setIsSending(false);
                setStatus("Ready");
                setStreamingThought("");
                setStreamingDelta("");
                setStreamingTool("");
                setStreamingAgent("");
                void loadConversations();
              } else if (currentEvent === "error") {
                toast.error(data.error ?? "Streaming error");
                setIsStreamingActive(false);
                setIsSending(false);
              }
            } catch (err) {
              console.error("SSE parse error:", err);
            }
          }
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Streaming failed";
      setStatus(message);
      toast.error(`Error: ${message}`);
      setIsStreamingActive(false);
      setIsSending(false);
    }
  };

  return (
    <ConversationContext.Provider
      value={{
        conversations,
        setConversations,
        activeConversationId,
        setActiveConversationId,
        messages,
        setMessages,
        currentExecutionSteps,
        editingConversationId,
        setEditingConversationId,
        editingTitle,
        setEditingTitle,
        conversationGroups,
        streamingThought,
        streamingDelta,
        streamingStatus,
        streamingTool,
        streamingAgent,
        isStreamingActive,
        loadConversations,
        loadMessages,
        createConversation,
        deleteConversation,
        renameConversation,
        sendMessage,
      }}
    >
      {children}
    </ConversationContext.Provider>
  );
};

export const useConversation = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error("useConversation must be used within a ConversationProvider");
  }
  return context;
};

export const useConversations = useConversation;
