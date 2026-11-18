"use client";

import Link from "next/navigation";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import {
  Users,
  CalendarCheck,
  Stethoscope,
  BarChart3,
  ShieldAlert,
  Clock,
  HeartPulse,
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { role } = useAuth();

  const navItems = [
    // Receptionist Routes
    {
      label: "Clinic Live Queue",
      href: "/receptionist",
      icon: CalendarCheck,
      roles: ["receptionist", "admin"],
    },
    {
      label: "Patient Registry",
      href: "/receptionist/patients",
      icon: Users,
      roles: ["receptionist", "admin"],
    },
    // Doctor Routes
    {
      label: "Today's Patient Queue",
      href: "/doctor",
      icon: Stethoscope,
      roles: ["doctor"],
    },
    // Admin Routes
    {
      label: "Operational Analytics",
      href: "/admin",
      icon: BarChart3,
      roles: ["admin"],
    },
    {
      label: "HIPAA Audit Trail",
      href: "/admin/audit",
      icon: ShieldAlert,
      roles: ["admin"],
    },
    {
      label: "Doctor Rosters",
      href: "/admin/schedules",
      icon: Clock,
      roles: ["admin"],
    },
  ];

  const visibleItems = navItems.filter(
    (item) => !role || item.roles.includes(role)
  );

  return (
    <aside className="w-64 shrink-0 border-r border-clinic-border bg-clinic-surface flex flex-col justify-between p-4">
      <div className="space-y-6">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-clinic-text-secondary px-3 block mb-2">
            Workspace Navigation
          </span>
          <nav className="space-y-1">
            {visibleItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-medium transition ${
                    isActive
                      ? "bg-clinic-accent-muted text-clinic-primary font-semibold border border-clinic-border"
                      : "text-clinic-text-secondary hover:bg-clinic-accent-subtle hover:text-clinic-text-primary"
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 shrink-0 ${
                      isActive ? "text-clinic-primary" : "text-clinic-text-secondary"
                    }`}
                  />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Clinical Triage Protocol Reminder */}
        <div className="rounded-xl border border-clinic-border bg-clinic-canvas p-3 shadow-clinical">
          <div className="flex items-center gap-2 text-clinic-primary">
            <HeartPulse className="h-4 w-4" />
            <span className="text-xs font-semibold">Triage Protocol</span>
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-clinic-text-secondary">
            Intake vitals are mandatory prior to doctor consultation. All medical record access is logged for HIPAA compliance.
          </p>
        </div>
      </div>

      {/* Version badge */}
      <div className="border-t border-clinic-border pt-3 text-[11px] text-clinic-text-secondary flex justify-between items-center px-1">
        <span>ClinicFlow Core</span>
        <span className="font-mono text-[10px] bg-clinic-accent-subtle px-1.5 py-0.5 rounded border border-clinic-border">
          v1.0.0 (AWS)
        </span>
      </div>
    </aside>
  );
}
