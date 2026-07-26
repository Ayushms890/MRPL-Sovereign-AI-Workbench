"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/auth-context";
import { Building2, Check, AlertCircle, ShieldCheck, ArrowRight, XCircle } from "lucide-react";
import toast from "react-hot-toast";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface JoinPageProps {
  params: Promise<{
    token: string;
  }>;
}

interface InviteDetails {
  token: string;
  workspace_id: string;
  workspace_name: string;
  invited_email: string;
  role: string;
  status: string;
  already_member: boolean;
  user_role: string | null;
  is_owner: boolean;
}

export default function JoinWorkspacePage({ params }: JoinPageProps) {
  const resolvedParams = use(params);
  const token = resolvedParams.token;
  const router = useRouter();
  const { token: authToken, isLoaded, isSignedIn } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inviteDetails, setInviteDetails] = useState<InviteDetails | null>(null);
  const [isAccepting, setIsAccepting] = useState(false);

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      router.push(`/auth?next=/join/${token}`);
      return;
    }

    const fetchInviteDetails = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_URL}/workspaces/invites/${token}`, {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Invalid or expired invitation token.");
        }
        setInviteDetails(data);
      } catch (err: any) {
        setError(err.message || "Could not load invitation details.");
      } finally {
        setLoading(false);
      }
    };

    fetchInviteDetails();
  }, [isLoaded, isSignedIn, token, authToken, router]);

  const handleAccept = async () => {
    try {
      setIsAccepting(true);
      const res = await fetch(`${API_URL}/workspaces/invites/${token}/accept`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to accept workspace invitation.");
      }
      toast.success(`Joined ${inviteDetails?.workspace_name || "workspace"}!`);
      router.push("/chat");
    } catch (err: any) {
      toast.error(err.message || "Failed to accept invitation");
      setError(err.message);
    } finally {
      setIsAccepting(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "#0f172a",
        color: "#f8fafc",
        fontFamily: "'Plus Jakarta Sans', sans-serif",
        padding: "24px",
      }}
    >
      <div
        style={{
          maxWidth: "460px",
          width: "100%",
          background: "#1e293b",
          padding: "32px",
          borderRadius: "16px",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
          textAlign: "center",
        }}
      >
        {/* Header Icon */}
        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "16px",
            background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 20px auto",
            boxShadow: "0 8px 20px rgba(99, 102, 241, 0.3)",
          }}
        >
          <Building2 size={28} style={{ color: "#ffffff" }} />
        </div>

        <h1 style={{ fontSize: "22px", fontWeight: "700", margin: "0 0 6px 0", color: "#f8fafc" }}>
          Workspace Invitation
        </h1>

        {loading && (
          <p style={{ color: "#94a3b8", fontSize: "14px", marginTop: "12px" }}>
            Verifying invitation token...
          </p>
        )}

        {error && (
          <div style={{ marginTop: "20px" }}>
            <div
              style={{
                padding: "14px 16px",
                borderRadius: "10px",
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#f87171",
                fontSize: "13px",
                marginBottom: "24px",
                textAlign: "left",
                display: "flex",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <div>{error}</div>
            </div>
            <button
              onClick={() => router.push("/chat")}
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "8px",
                background: "#6366f1",
                color: "#ffffff",
                fontSize: "14px",
                fontWeight: "600",
                border: "none",
                cursor: "pointer",
              }}
            >
              Return to Workspaces
            </button>
          </div>
        )}

        {!loading && !error && inviteDetails && (
          <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Invite Details Box */}
            <div
              style={{
                background: "#0f172a",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "12px",
                padding: "18px",
                textAlign: "left",
                display: "flex",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                <span style={{ color: "#94a3b8" }}>Target Workspace:</span>
                <strong style={{ color: "#f8fafc", fontWeight: "700" }}>
                  {inviteDetails.workspace_name}
                </strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                <span style={{ color: "#94a3b8" }}>Offered Role:</span>
                <span
                  style={{
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "rgba(99, 102, 241, 0.2)",
                    color: "#818cf8",
                    fontWeight: "700",
                    fontSize: "11px",
                    textTransform: "uppercase",
                  }}
                >
                  {inviteDetails.role}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                <span style={{ color: "#94a3b8" }}>Invited Email:</span>
                <span style={{ color: "#cbd5e1" }}>{inviteDetails.invited_email}</span>
              </div>
            </div>

            {/* Owner or Existing Member Notice */}
            {inviteDetails.already_member ? (
              <div>
                <div
                  style={{
                    padding: "14px 16px",
                    borderRadius: "10px",
                    background: inviteDetails.is_owner
                      ? "rgba(245, 158, 11, 0.1)"
                      : "rgba(59, 130, 246, 0.1)",
                    border: inviteDetails.is_owner
                      ? "1px solid rgba(245, 158, 11, 0.3)"
                      : "1px solid rgba(59, 130, 246, 0.3)",
                    color: inviteDetails.is_owner ? "#fbbf24" : "#60a5fa",
                    fontSize: "13px",
                    marginBottom: "20px",
                    textAlign: "left",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <ShieldCheck size={20} />
                  <div>
                    <strong>
                      {inviteDetails.is_owner
                        ? "You are the Owner of this workspace!"
                        : `You are already a ${inviteDetails.user_role?.toUpperCase()} in this workspace.`}
                    </strong>
                    <div style={{ fontSize: "12px", opacity: 0.9, marginTop: "2px" }}>
                      Re-joining is not required.
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => router.push("/chat")}
                  style={{
                    width: "100%",
                    padding: "12px",
                    borderRadius: "8px",
                    background: "#6366f1",
                    color: "#ffffff",
                    fontSize: "14px",
                    fontWeight: "600",
                    border: "none",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                  }}
                >
                  Go to Workspace <ArrowRight size={16} />
                </button>
              </div>
            ) : (
              /* New Member Confirmation Actions */
              <div>
                <p style={{ fontSize: "13px", color: "#94a3b8", margin: "0 0 20px 0" }}>
                  Accepting this invite will add your account to{" "}
                  <strong>{inviteDetails.workspace_name}</strong> as a{" "}
                  <strong>{inviteDetails.role}</strong>.
                </p>

                <div style={{ display: "flex", gap: "12px" }}>
                  <button
                    type="button"
                    onClick={() => router.push("/chat")}
                    style={{
                      flex: 1,
                      padding: "12px",
                      borderRadius: "8px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      color: "#94a3b8",
                      fontSize: "14px",
                      fontWeight: "600",
                      cursor: "pointer",
                    }}
                  >
                    Decline
                  </button>
                  <button
                    type="button"
                    onClick={handleAccept}
                    disabled={isAccepting}
                    style={{
                      flex: 2,
                      padding: "12px",
                      borderRadius: "8px",
                      background: "#10b981",
                      color: "#ffffff",
                      fontSize: "14px",
                      fontWeight: "600",
                      border: "none",
                      cursor: isAccepting ? "not-allowed" : "pointer",
                      opacity: isAccepting ? 0.7 : 1,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "8px",
                    }}
                  >
                    <Check size={18} />
                    {isAccepting ? "Joining..." : "Accept & Join"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
