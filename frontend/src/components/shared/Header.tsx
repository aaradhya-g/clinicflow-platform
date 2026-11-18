"use client";

import { useAuth } from "@/hooks/use-auth";
import { Activity, LogOut, ShieldCheck, Stethoscope, UserCheck } from "lucide-react";
import { UserRole } from "@/types";

export function Header() {
  const { user, role, demoLogin, logout, isLoading } = useAuth();

  const getRoleIcon = () => {
    switch (role) {
      case "doctor":
        return <Stethoscope className="h-4 w-4 text-clinic-primary" />;
      case "admin":
        return <ShieldCheck className="h-4 w-4 text-clinic-primary" />;
      default:
        return <UserCheck className="h-4 w-4 text-clinic-primary" />;
    }
  };

  const getRoleLabel = () => {
    switch (role) {
      case "doctor":
        return "Attending Physician";
      case "admin":
        return "Clinical Administrator";
      default:
        return "Receptionist & Triage Desk";
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-clinic-border bg-clinic-canvas px-6 shadow-clinical">
      {/* Brand & Clinic Indicator */}
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-clinic-border bg-clinic-accent-subtle text-clinic-primary">
          <Activity className="h-5 w-5 stroke-[2.2]" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-base tracking-tight text-clinic-text-primary">
              ClinicFlow
            </span>
            <span className="rounded-full bg-clinic-accent-muted px-2 py-0.5 text-[11px] font-semibold text-clinic-primary border border-clinic-border">
              Health Center
            </span>
          </div>
          <span className="text-[11px] text-clinic-text-secondary block -mt-0.5">
            EHR & Triage Operations
          </span>
        </div>
      </div>

      {/* Center Demo Role Switcher Quick Bar */}
      <div className="hidden md:flex items-center gap-1.5 rounded-lg border border-clinic-border bg-clinic-surface p-1">
        <span className="text-[11px] font-semibold text-clinic-text-secondary px-2 uppercase tracking-wider">
          Demo Switch:
        </span>
        <button
          onClick={() => demoLogin("receptionist")}
          disabled={isLoading || role === "receptionist"}
          className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition ${
            role === "receptionist"
              ? "bg-clinic-primary text-white shadow-xs"
              : "text-clinic-text-secondary hover:bg-clinic-accent-subtle hover:text-clinic-text-primary"
          }`}
        >
          <UserCheck className="h-3.5 w-3.5" />
          Receptionist
        </button>
        <button
          onClick={() => demoLogin("doctor")}
          disabled={isLoading || role === "doctor"}
          className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition ${
            role === "doctor"
              ? "bg-clinic-primary text-white shadow-xs"
              : "text-clinic-text-secondary hover:bg-clinic-accent-subtle hover:text-clinic-text-primary"
          }`}
        >
          <Stethoscope className="h-3.5 w-3.5" />
          Dr. Chen
        </button>
        <button
          onClick={() => demoLogin("admin")}
          disabled={isLoading || role === "admin"}
          className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition ${
            role === "admin"
              ? "bg-clinic-primary text-white shadow-xs"
              : "text-clinic-text-secondary hover:bg-clinic-accent-subtle hover:text-clinic-text-primary"
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          Admin
        </button>
      </div>

      {/* User Status & Logout */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex flex-col text-right">
          <span className="text-xs font-semibold text-clinic-text-primary">
            {user?.full_name || "Healthcare Staff"}
          </span>
          <div className="flex items-center justify-end gap-1 text-[11px] text-clinic-text-secondary">
            {getRoleIcon()}
            <span>{getRoleLabel()}</span>
          </div>
        </div>

        <button
          onClick={logout}
          title="Sign Out"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-clinic-border bg-clinic-canvas text-clinic-text-secondary transition hover:border-clinic-primary hover:bg-clinic-accent-subtle hover:text-clinic-primary"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
