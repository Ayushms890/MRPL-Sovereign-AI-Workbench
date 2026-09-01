"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { FormEvent } from "react";
import { createApiClient } from "../lib/api-client";
import { useAuth } from "./auth-context";

export type SupportedProvider = "gemini" | "groq" | "nvidia" | "ollama";

type ApiKeysContextType = {
  apiKeyProvider: SupportedProvider;
  setApiKeyProvider: (provider: SupportedProvider) => void;
  apiKeyValue: string;
  setApiKeyValue: (val: string) => void;
  ollamaBaseUrl: string;
  setOllamaBaseUrl: (val: string) => void;
  apiKeyStatus: string;
  setApiKeyStatus: (status: string) => void;
  isSavingApiKey: boolean;
  configuredProviders: string[];
  preferredProvider: string | null;
  setPreferredProvider: (provider: string | null) => void;
  preferredModel: string | null;
  setPreferredModel: (model: string | null) => void;
  activeModelLabel: string;
  saveApiKey: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  deleteApiKey: (providerToDelete: SupportedProvider) => Promise<void>;
  updatePreferences: (provider?: string | null, model?: string | null) => Promise<void>;
};

const ApiKeysContext = createContext<ApiKeysContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const ApiKeysProvider = ({ children }: { children: React.ReactNode }) => {
  const { getToken, logout, isAuthenticated } = useAuth();

  const [apiKeyProvider, setApiKeyProvider] = useState<SupportedProvider>("nvidia");
  const [apiKeyValue, setApiKeyValue] = useState("");
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState("http://localhost:11434");
  const [apiKeyStatus, setApiKeyStatus] = useState("Configure your API keys");
  const [isSavingApiKey, setIsSavingApiKey] = useState(false);
  const [configuredProviders, setConfiguredProviders] = useState<string[]>([]);
  const [preferredProvider, setPreferredProvider] = useState<string | null>(null);
  const [preferredModel, setPreferredModel] = useState<string | null>(null);

  const activeModelLabel = (() => {
    if (preferredProvider === "nvidia") return `NVIDIA NIM (${preferredModel || "meta/llama-3.3-70b-instruct"})`;
    if (preferredProvider === "ollama") return `Ollama (${preferredModel || "llama3.1"})`;
    if (preferredProvider === "groq") return `Groq Client (${preferredModel || "llama-3.3-70b"})`;
    if (preferredProvider === "gemini") return `Google Gemini (${preferredModel || "gemini-3.5-flash"})`;
    return `Default Model (${preferredModel || "gemini-3.5-flash"})`;
  })();

  useEffect(() => {
    if (!isAuthenticated) return;

    let isMounted = true;

    async function loadData() {
      const currentToken = await getToken();
      if (!currentToken || !isMounted) return;

      // Load profile for preferred provider & model
      fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
        .then((res) => {
          if (!res.ok) {
            if (res.status === 401) { logout(); return null; }
            throw new Error("Profile request failed");
          }
          return res.json();
        })
        .then((data) => {
          if (isMounted) {
            if (data?.preferred_provider) {
              setPreferredProvider(data.preferred_provider);
            }
            if (data?.preferred_model) {
              setPreferredModel(data.preferred_model);
            }
          }
        })
        .catch((err) => console.error("Could not fetch user profile", err));

      // Load configured API keys
      fetch(`${API_URL}/users/me/api-keys`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
        .then((res) => {
          if (!res.ok) {
            if (res.status === 401) { logout(); return null; }
            throw new Error("API keys request failed");
          }
          return res.json();
        })
        .then((data) => {
          if (isMounted && data?.providers) {
            const list = data.providers.map((p: any) => p.provider);
            setConfiguredProviders(list);
          }
        })
        .catch((err) => console.error("Could not fetch api keys", err));
    }

    void loadData();

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, getToken, logout]);

  async function updatePreferences(provider?: string | null, model?: string | null) {
    const api = createApiClient(getToken);
    setIsSavingApiKey(true);
    try {
      const payload: { preferred_provider?: string | null; preferred_model?: string | null } = {};
      if (provider !== undefined) payload.preferred_provider = provider;
      if (model !== undefined) payload.preferred_model = model;

      const res = await api<{ preferred_provider: string | null; preferred_model: string | null }>("/users/me/preferences", {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      if (provider !== undefined) setPreferredProvider(res.preferred_provider);
      if (model !== undefined) setPreferredModel(res.preferred_model);
      setApiKeyStatus("Preferences updated successfully");
    } catch (error) {
      setApiKeyStatus(error instanceof Error ? error.message : "Could not update preferences");
    } finally {
      setIsSavingApiKey(false);
    }
  }

  async function saveApiKey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (apiKeyProvider === "ollama" && !ollamaBaseUrl.trim()) {
      setApiKeyStatus("Enter an Ollama base URL before saving");
      return;
    }
    if (apiKeyProvider !== "ollama" && !apiKeyValue.trim()) {
      setApiKeyStatus("Enter a key before saving");
      return;
    }
    const api = createApiClient(getToken);
    setIsSavingApiKey(true);
    setApiKeyStatus(apiKeyProvider === "ollama" ? "Saving Ollama URL..." : "Saving key...");
    try {
      const body =
        apiKeyProvider === "ollama"
          ? { provider: apiKeyProvider, base_url: ollamaBaseUrl.trim() }
          : { provider: apiKeyProvider, api_key: apiKeyValue.trim() };
      const response = await api<{ provider: string; created_at: string }>("/users/me/api-keys", {
        method: "POST",
        body: JSON.stringify(body),
      });
      setApiKeyValue("");
      setApiKeyStatus(
        response.provider === "ollama"
          ? "Ollama base URL saved successfully"
          : `${response.provider.toUpperCase()} API key saved successfully`
      );

      const nextProviders = [...new Set([...configuredProviders, apiKeyProvider])];
      setConfiguredProviders(nextProviders);
      setPreferredProvider(apiKeyProvider);
      await updatePreferences(apiKeyProvider, preferredModel);
    } catch (error) {
      setApiKeyStatus(error instanceof Error ? error.message : "Could not save key");
    } finally {
      setIsSavingApiKey(false);
    }
  }

  async function deleteApiKey(providerToDelete: SupportedProvider) {
    const api = createApiClient(getToken);
    setIsSavingApiKey(true);
    setApiKeyStatus("Deleting key...");
    try {
      await api(`/users/me/api-keys/${providerToDelete}`, { method: "DELETE" });
      setApiKeyStatus(`${providerToDelete.toUpperCase()} key deleted`);

      const nextProviders = configuredProviders.filter((p) => p !== providerToDelete);
      setConfiguredProviders(nextProviders);
      const newPreferred = nextProviders[0] ?? null;
      setPreferredProvider(newPreferred);
      if (preferredProvider === providerToDelete) {
        await updatePreferences(newPreferred, preferredModel);
      }
    } catch (error) {
      setApiKeyStatus(error instanceof Error ? error.message : "Could not delete key");
    } finally {
      setIsSavingApiKey(false);
    }
  }

  return (
    <ApiKeysContext.Provider
      value={{
        apiKeyProvider,
        setApiKeyProvider,
        apiKeyValue,
        setApiKeyValue,
        ollamaBaseUrl,
        setOllamaBaseUrl,
        apiKeyStatus,
        setApiKeyStatus,
        isSavingApiKey,
        configuredProviders,
        preferredProvider,
        setPreferredProvider,
        preferredModel,
        setPreferredModel,
        activeModelLabel,
        saveApiKey,
        deleteApiKey,
        updatePreferences,
      }}
    >
      {children}
    </ApiKeysContext.Provider>
  );
};

export function useApiKeys() {
  const context = useContext(ApiKeysContext);
  if (context === undefined) {
    throw new Error("useApiKeys must be used within an ApiKeysProvider");
  }
  return context;
}

export { ApiKeysContext };
