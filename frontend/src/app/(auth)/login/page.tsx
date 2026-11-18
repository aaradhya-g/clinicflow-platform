"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { Activity, ShieldCheck, Stethoscope, UserCheck, AlertCircle } from "lucide-react";
import { UserRole } from "@/types";

export default function LoginPage() {
  const { login, demoLogin, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeDemoRole, setActiveDemoRole] = useState<UserRole | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await login(email, password);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Invalid login credentials. Please try again.");
    }
  };

  const handleDemoSwitch = async (role: UserRole) => {
    setActiveDemoRole(role);
    setErrorMsg(null);
    try {
      await demoLogin(role);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Could not switch to demo role.");
    } finally {
      setActiveDemoRole(null);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-clinic-canvas px-4 py-12">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-clinic-accent-subtle border border-clinic-border text-clinic-primary shadow-clinical">
            <Activity className="h-8 w-8 stroke-[2.2]" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-clinic-text-primary">
            ClinicFlow
          </h1>
          <p className="mt-1 text-sm text-clinic-text-secondary">
            Clinical Appointment, Triage & Electronic Health Record Platform
          </p>
        </div>

        {/* Quick Demo Role Switcher Strip */}
        <div className="mt-6 rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-clinic-border">
            <span className="text-xs font-semibold uppercase tracking-wider text-clinic-text-secondary">
              Instant 1-Click Demo Evaluation
            </span>
            <span className="inline-flex items-center rounded-full bg-clinic-accent-muted px-2 py-0.5 text-[10px] font-semibold text-clinic-primary">
              Pre-Seeded
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleDemoSwitch("receptionist")}
              disabled={isLoading}
              className="flex flex-col items-center justify-center rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center transition hover:border-clinic-primary hover:bg-clinic-accent-subtle active:scale-[0.98]"
            >
              <UserCheck className="h-5 w-5 text-clinic-primary" />
              <span className="mt-1 text-xs font-semibold text-clinic-text-primary">Receptionist</span>
              <span className="text-[10px] text-clinic-text-secondary">Queue & Triage</span>
            </button>

            <button
              type="button"
              onClick={() => handleDemoSwitch("doctor")}
              disabled={isLoading}
              className="flex flex-col items-center justify-center rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center transition hover:border-clinic-primary hover:bg-clinic-accent-subtle active:scale-[0.98]"
            >
              <Stethoscope className="h-5 w-5 text-clinic-primary" />
              <span className="mt-1 text-xs font-semibold text-clinic-text-primary">Physician</span>
              <span className="text-[10px] text-clinic-text-secondary">Dr. Sarah Chen</span>
            </button>

            <button
              type="button"
              onClick={() => handleDemoSwitch("admin")}
              disabled={isLoading}
              className="flex flex-col items-center justify-center rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center transition hover:border-clinic-primary hover:bg-clinic-accent-subtle active:scale-[0.98]"
            >
              <ShieldCheck className="h-5 w-5 text-clinic-primary" />
              <span className="mt-1 text-xs font-semibold text-clinic-text-primary">Admin</span>
              <span className="text-[10px] text-clinic-text-secondary">Audit & KPIs</span>
            </button>
          </div>
        </div>

        {/* Credentials Form */}
        <div className="mt-6 rounded-xl border border-clinic-border bg-clinic-surface p-6 shadow-clinical">
          {errorMsg && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-clinic-text-secondary uppercase tracking-wider">
                Clinical Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="doctor.chen@clinicflow.med"
                className="mt-1 block w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3.5 py-2.5 text-sm text-clinic-text-primary placeholder:text-slate-400 focus:border-clinic-primary focus:outline-none focus:ring-1 focus:ring-clinic-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-clinic-text-secondary uppercase tracking-wider">
                Staff Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="mt-1 block w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3.5 py-2.5 text-sm text-clinic-text-primary placeholder:text-slate-400 focus:border-clinic-primary focus:outline-none focus:ring-1 focus:ring-clinic-primary"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="mt-2 flex w-full items-center justify-center rounded-lg bg-clinic-primary px-4 py-2.5 text-sm font-semibold text-white shadow-clinical transition hover:bg-clinic-primary-hover disabled:opacity-50"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Signing In...</span>
                </div>
              ) : (
                "Sign In to Clinic Workspace"
              )}
            </button>
          </form>
        </div>

        {/* Compliance Footer */}
        <p className="mt-6 text-center text-xs text-clinic-text-secondary">
          Protected by HIPAA Security Standards &bull; 256-Bit TLS Encryption
        </p>
      </div>
    </div>
  );
}
