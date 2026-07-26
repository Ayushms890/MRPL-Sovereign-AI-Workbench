"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "./auth-context";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Workspace {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
  my_role: "owner" | "member" | "viewer" | string | null;
}

export interface WorkspaceMember {
  user_id: string;
  email: string;
  name: string;
  role: "owner" | "member" | "viewer" | string;
  joined_at: string;
}

export interface WorkspaceInvite {
  id: string;
  workspace_id: string;
  email: string;
  role: string;
  token: string;
  status: string;
  expires_at: string;
  created_at: string;
}

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  activeWorkspace: Workspace | null;
  myRole: "owner" | "member" | "viewer" | string | null;
  members: WorkspaceMember[];
  loading: boolean;
  error: string | null;
  switchWorkspace: (workspaceId: string) => void;
  createWorkspace: (name: string) => Promise<Workspace>;
  inviteMember: (email: string, role: "member" | "viewer") => Promise<WorkspaceInvite>;
  updateMemberRole: (userId: string, role: "owner" | "member" | "viewer") => Promise<void>;
  removeMember: (userId: string) => Promise<void>;
  leaveWorkspace: (workspaceId: string) => Promise<void>;
  refreshWorkspaces: () => Promise<void>;
  refreshMembers: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { token, isSignedIn, isLoaded } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkspaces = useCallback(async () => {
    if (!token || !isSignedIn) {
      setWorkspaces([]);
      setActiveWorkspaceId(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/workspaces`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error("Failed to load workspaces");
      }
      const data: Workspace[] = await res.json();
      setWorkspaces(data);

      if (data.length > 0) {
        const savedWsId = typeof window !== "undefined" ? localStorage.getItem("active_workspace_id") : null;
        const exists = data.find((w) => w.id === savedWsId);
        const selectedId = exists ? exists.id : data[0].id;
        setActiveWorkspaceId(selectedId);
        if (typeof window !== "undefined") {
          localStorage.setItem("active_workspace_id", selectedId);
        }
      }
    } catch (err: any) {
      loggerError("Error fetching workspaces", err);
      setError(err.message || "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  }, [token, isSignedIn]);

  useEffect(() => {
    if (isLoaded) {
      fetchWorkspaces();
    }
  }, [isLoaded, fetchWorkspaces]);

  const activeWorkspace = useMemo(() => {
    return workspaces.find((w) => w.id === activeWorkspaceId) || null;
  }, [workspaces, activeWorkspaceId]);

  const myRole = useMemo(() => {
    return activeWorkspace?.my_role || null;
  }, [activeWorkspace]);

  const fetchMembers = useCallback(async () => {
    if (!token || !activeWorkspaceId) {
      setMembers([]);
      return;
    }
    try {
      const res = await fetch(`${API_URL}/workspaces/${activeWorkspaceId}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: WorkspaceMember[] = await res.json();
        setMembers(data);
      }
    } catch (err) {
      loggerError("Error fetching workspace members", err);
    }
  }, [token, activeWorkspaceId]);

  useEffect(() => {
    if (activeWorkspaceId) {
      fetchMembers();
    }
  }, [activeWorkspaceId, fetchMembers]);

  const switchWorkspace = (workspaceId: string) => {
    setActiveWorkspaceId(workspaceId);
    if (typeof window !== "undefined") {
      localStorage.setItem("active_workspace_id", workspaceId);
    }
  };

  const createWorkspace = async (name: string): Promise<Workspace> => {
    if (!token) throw new Error("Not authenticated");
    const res = await fetch(`${API_URL}/workspaces`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to create workspace");
    }

    const newWs: Workspace = data;
    setWorkspaces((prev) => [newWs, ...prev]);
    setActiveWorkspaceId(newWs.id);
    if (typeof window !== "undefined") {
      localStorage.setItem("active_workspace_id", newWs.id);
    }
    return newWs;
  };

  const inviteMember = async (email: string, role: "member" | "viewer"): Promise<WorkspaceInvite> => {
    if (!token || !activeWorkspaceId) throw new Error("No active workspace");
    const res = await fetch(`${API_URL}/workspaces/${activeWorkspaceId}/invites`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, role }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to send invitation");
    }
    return data as WorkspaceInvite;
  };

  const updateMemberRole = async (userId: string, role: "owner" | "member" | "viewer") => {
    if (!token || !activeWorkspaceId) throw new Error("No active workspace");
    const res = await fetch(`${API_URL}/workspaces/${activeWorkspaceId}/members/${userId}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ role }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to update member role");
    }
    await fetchMembers();
  };

  const removeMember = async (userId: string) => {
    if (!token || !activeWorkspaceId) throw new Error("No active workspace");
    const res = await fetch(`${API_URL}/workspaces/${activeWorkspaceId}/members/${userId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to remove member");
    }
    await fetchMembers();
  };

  const leaveWorkspace = async (workspaceId: string) => {
    if (!token) throw new Error("Not authenticated");
    const res = await fetch(`${API_URL}/workspaces/${workspaceId}/leave`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to leave workspace");
    }
    await fetchWorkspaces();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspaceId,
        activeWorkspace,
        myRole,
        members,
        loading,
        error,
        switchWorkspace,
        createWorkspace,
        inviteMember,
        updateMemberRole,
        removeMember,
        leaveWorkspace,
        refreshWorkspaces: fetchWorkspaces,
        refreshMembers: fetchMembers,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}

function loggerError(msg: string, err: any) {
  if (process.env.NODE_ENV !== "production") {
    console.error(msg, err);
  }
}
