"use client";

import React, { useState } from "react";
import { useChat } from "../chat-context";
import {
  X,
  UserPlus,
  Users,
  Building2,
  Trash2,
  Check,
  Plus,
  Copy,
  AlertCircle,
  Shield,
  Mail,
  LogOut,
} from "lucide-react";
import toast from "react-hot-toast";

interface WorkspaceMembersModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WorkspaceMembersModal({ isOpen, onClose }: WorkspaceMembersModalProps) {
  const {
    workspaces,
    activeWorkspaceId,
    activeWorkspace,
    myRole,
    members,
    switchWorkspace,
    createWorkspace,
    inviteMember,
    updateMemberRole,
    removeMember,
    leaveWorkspace,
  } = useChat();

  const [activeTab, setActiveTab] = useState<"members" | "workspaces">("members");
  const [newWsName, setNewWsName] = useState("");
  const [isCreatingWs, setIsCreatingWs] = useState(false);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "viewer">("member");
  const [isInviting, setIsInviting] = useState(false);
  const [generatedLink, setGeneratedLink] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  if (!isOpen) return null;

  const handleCreateWs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim()) return;
    try {
      setIsCreatingWs(true);
      await createWorkspace(newWsName.trim());
      setNewWsName("");
      toast.success("Workspace created successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to create workspace");
    } finally {
      setIsCreatingWs(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    try {
      setIsInviting(true);
      setGeneratedLink(null);
      const invite = await inviteMember(inviteEmail.trim(), inviteRole);
      setInviteEmail("");
      if (invite && invite.token) {
        const joinUrl = `${window.location.origin}/join/${invite.token}`;
        setGeneratedLink(joinUrl);
        navigator.clipboard.writeText(joinUrl);
        toast.success("Invite link generated & copied to clipboard!");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to create invite link");
    } finally {
      setIsInviting(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: "owner" | "member" | "viewer") => {
    try {
      await updateMemberRole(userId, newRole);
      toast.success("Member role updated");
    } catch (err: any) {
      toast.error(err.message || "Failed to update role");
    }
  };

  const handleRemove = async (userId: string) => {
    if (!confirm("Are you sure you want to remove this member from the workspace?")) return;
    try {
      await removeMember(userId);
      toast.success("Member removed");
    } catch (err: any) {
      toast.error(err.message || "Failed to remove member");
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Left Sidebar matching Settings Modal */}
        <div className="modal-sidebar">
          <h3>Workspaces</h3>
          <nav className="modal-nav">
            <button
              type="button"
              className={`modal-nav-btn ${activeTab === "members" ? "active" : ""}`}
              onClick={() => setActiveTab("members")}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <Users size={14} />
              <span>Members & Invites</span>
            </button>
            <button
              type="button"
              className={`modal-nav-btn ${activeTab === "workspaces" ? "active" : ""}`}
              onClick={() => setActiveTab("workspaces")}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <Building2 size={14} />
              <span>Switch Workspace</span>
            </button>
          </nav>
        </div>

        {/* Right Content Body matching Settings Modal */}
        <div className="modal-body">
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            <X size={16} />
          </button>

          {/* Tab 1: Members & Invites */}
          {activeTab === "members" && (
            <div className="modal-tab-panel">
              <h2>Members & Invitations</h2>
              <p className="tab-description">
                Workspace: <strong>{activeWorkspace?.name || "Active Workspace"}</strong> • Your Role:{" "}
                <span style={{ textTransform: "uppercase", fontWeight: 700 }}>{myRole}</span>
              </p>

              {myRole === "owner" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  {/* Send Email Invite Form */}
                  <form onSubmit={handleInvite} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <label>
                      Invite Team Member
                      <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
                        <input
                          type="email"
                          required
                          placeholder="colleague@example.com"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          style={{ flex: 1 }}
                        />
                        <select
                          value={inviteRole}
                          onChange={(e) => setInviteRole(e.target.value as "member" | "viewer")}
                          style={{ width: "130px" }}
                        >
                          <option value="member">Member</option>
                          <option value="viewer">Viewer</option>
                        </select>
                        <button
                          type="submit"
                          disabled={isInviting || !inviteEmail.trim()}
                          style={{
                            padding: "0 18px",
                            background: "var(--accent)",
                            color: "#ffffff",
                            border: "none",
                            borderRadius: "8px",
                            fontWeight: 600,
                            fontSize: "0.85rem",
                            cursor: isInviting || !inviteEmail.trim() ? "not-allowed" : "pointer",
                            opacity: isInviting || !inviteEmail.trim() ? 0.6 : 1,
                            whiteSpace: "nowrap",
                            height: "40px",
                          }}
                        >
                          {isInviting ? "Creating..." : "Create Link"}
                        </button>
                      </div>
                    </label>

                    {/* Generated Invite Link Box */}
                    {generatedLink && (
                      <div
                        style={{
                          padding: "12px 14px",
                          borderRadius: "8px",
                          background: "rgba(37, 99, 235, 0.08)",
                          border: "1px solid rgba(37, 99, 235, 0.25)",
                          color: "#1d4ed8",
                          fontSize: "0.82rem",
                        }}
                      >
                        <div style={{ fontWeight: 600, marginBottom: "6px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <Check size={14} style={{ color: "#16a34a" }} />
                          Invite link created and copied to clipboard! Share it with your team:
                        </div>
                        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <input
                            type="text"
                            readOnly
                            value={generatedLink}
                            style={{
                              flex: 1,
                              height: "34px",
                              fontSize: "0.8rem",
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(generatedLink);
                              setCopiedLink(true);
                              toast.success("Join link copied to clipboard");
                              setTimeout(() => setCopiedLink(false), 2000);
                            }}
                            style={{
                              height: "34px",
                              padding: "0 12px",
                              borderRadius: "6px",
                              background: "var(--accent)",
                              color: "#ffffff",
                              border: "none",
                              fontSize: "0.8rem",
                              cursor: "pointer",
                              fontWeight: 600,
                              whiteSpace: "nowrap",
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            {copiedLink ? <Check size={14} /> : <Copy size={14} />}
                            {copiedLink ? "Copied" : "Copy Link"}
                          </button>
                        </div>
                      </div>
                    )}
                  </form>

                  {/* Members List */}
                  <div className="key-status-list">
                    <h4>Members List ({members.length})</h4>
                    <div className="key-checklist">
                      {members.map((m) => {
                        const isOwner = m.role === "owner";
                        return (
                          <div key={m.user_id} className="checklist-item">
                            <div className="provider-status-info">
                              <span className={`status-dot ${isOwner ? "active" : ""}`}></span>
                              <div>
                                <h5>{m.name || m.email}</h5>
                                <span>{m.email}</span>
                              </div>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              {isOwner ? (
                                <span
                                  style={{
                                    fontSize: "0.75rem",
                                    fontWeight: 700,
                                    color: "#1d4ed8",
                                    padding: "3px 8px",
                                    borderRadius: "4px",
                                    background: "#eff6ff",
                                    border: "1px solid #bfdbfe",
                                  }}
                                >
                                  OWNER
                                </span>
                              ) : (
                                <>
                                  <select
                                    value={m.role}
                                    onChange={(e) =>
                                      handleRoleChange(m.user_id, e.target.value as any)
                                    }
                                    style={{ width: "100px", height: "30px", fontSize: "0.8rem", padding: "0 6px" }}
                                  >
                                    <option value="member">Member</option>
                                    <option value="viewer">Viewer</option>
                                  </select>
                                  <button
                                    type="button"
                                    className="ghost btn-delete-key"
                                    onClick={() => handleRemove(m.user_id)}
                                    style={{ color: "#dc2626", border: "1px solid #fecaca" }}
                                    title="Remove Member"
                                  >
                                    <Trash2 size={13} />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="general-details-list">
                  <div className="detail-row">
                    <span>Your Workspace Role</span>
                    <strong style={{ textTransform: "uppercase" }}>{myRole}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Permissions</span>
                    <span>{myRole === "member" ? "Can send messages & upload docs" : "Read-only access"}</span>
                  </div>
                  <p style={{ margin: "12px 0 0", fontSize: "0.8rem", color: "var(--muted)" }}>
                    Only workspace owners can invite new team members or manage roles.
                  </p>

                  <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: "1px solid rgba(0, 0, 0, 0.08)", display: "flex", justifyContent: "flex-end" }}>
                    <button
                      type="button"
                      onClick={async () => {
                        if (!activeWorkspaceId) return;
                        if (confirm(`Are you sure you want to leave ${activeWorkspace?.name || "this workspace"}?`)) {
                          try {
                            await leaveWorkspace(activeWorkspaceId);
                            toast.success("You have left the workspace");
                            onClose();
                          } catch (err: any) {
                            toast.error(err.message || "Failed to leave workspace");
                          }
                        }
                      }}
                      style={{
                        padding: "8px 16px",
                        borderRadius: "6px",
                        background: "#fef2f2",
                        border: "1px solid #fecaca",
                        color: "#dc2626",
                        fontWeight: 600,
                        fontSize: "0.82rem",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <LogOut size={14} /> Leave Workspace
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Switch Workspace */}
          {activeTab === "workspaces" && (
            <div className="modal-tab-panel">
              <h2>Switch or Create Workspace</h2>
              <p className="tab-description">
                Select your active workspace context or create a new team workspace.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                <label>
                  Current Workspace
                  <select
                    value={activeWorkspaceId || ""}
                    onChange={(e) => switchWorkspace(e.target.value)}
                    style={{ marginTop: "6px" }}
                  >
                    {workspaces.map((ws) => (
                      <option key={ws.id} value={ws.id}>
                        {ws.name} ({ws.my_role ? ws.my_role.toUpperCase() : "MEMBER"})
                      </option>
                    ))}
                  </select>
                </label>

                <form onSubmit={handleCreateWs} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label>
                    Create New Workspace
                    <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
                      <input
                        type="text"
                        placeholder="New workspace name..."
                        value={newWsName}
                        onChange={(e) => setNewWsName(e.target.value)}
                        style={{ flex: 1 }}
                      />
                      <button
                        type="submit"
                        disabled={isCreatingWs || !newWsName.trim()}
                        style={{
                          padding: "0 18px",
                          background: "var(--accent)",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "8px",
                          fontWeight: 600,
                          fontSize: "0.85rem",
                          cursor: !newWsName.trim() ? "not-allowed" : "pointer",
                          opacity: !newWsName.trim() ? 0.6 : 1,
                          whiteSpace: "nowrap",
                          height: "40px",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <Plus size={16} /> Create
                      </button>
                    </div>
                  </label>
                </form>

                <div className="key-status-list">
                  <h4>Your Workspaces ({workspaces.length})</h4>
                  <div className="key-checklist">
                    {workspaces.map((ws) => (
                      <div key={ws.id} className="checklist-item">
                        <div className="provider-status-info">
                          <span className={`status-dot ${ws.id === activeWorkspaceId ? "active" : ""}`}></span>
                          <div>
                            <h5>{ws.name}</h5>
                            <span>{ws.id === activeWorkspaceId ? "Active Workspace" : "Joined"}</span>
                          </div>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--muted)", textTransform: "uppercase", fontWeight: 700 }}>
                            {ws.my_role}
                          </span>
                          {ws.id !== activeWorkspaceId && (
                            <button
                              type="button"
                              className="ghost btn-delete-key"
                              onClick={() => switchWorkspace(ws.id)}
                            >
                              Switch
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
