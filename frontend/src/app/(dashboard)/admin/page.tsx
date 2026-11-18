"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ClinicKPIs } from "@/types";
import {
  BarChart3,
  CalendarCheck,
  CheckCircle2,
  Clock,
  HeartPulse,
  ShieldCheck,
  TrendingUp,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";

export default function AdminAnalyticsPage() {
  const { data: kpis, isLoading } = useQuery<ClinicKPIs>({
    queryKey: ["clinicKPIs"],
    queryFn: async () => {
      const res = await apiClient.get<ClinicKPIs>("/analytics/kpis");
      return res.data;
    },
    refetchInterval: 15000,
  });

  if (isLoading || !kpis) {
    return (
      <div className="p-12 text-center text-xs text-clinic-text-secondary">
        <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent mb-2" />
        Aggregating clinic operational intelligence...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-clinic-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-clinic-primary" />
            Clinic Operational Analytics & Performance
          </h1>
          <p className="text-xs text-clinic-text-secondary mt-0.5">
            Real-time patient volumes, physician utilization rates, and insurance verification statistics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 text-xs font-semibold flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Live Clinic Telemetry
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Total Registered Patients</span>
            <Users className="h-4 w-4" />
          </div>
          <div className="mt-2 text-2xl font-bold text-clinic-text-primary font-mono">
            {kpis.total_patients}
          </div>
          <span className="text-[11px] text-clinic-text-secondary mt-1 block">
            Master Patient Index (MPI)
          </span>
        </div>

        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Today&apos;s Appointments</span>
            <CalendarCheck className="h-4 w-4 text-clinic-primary" />
          </div>
          <div className="mt-2 text-2xl font-bold text-clinic-primary font-mono">
            {kpis.today_appointments}
          </div>
          <span className="text-[11px] text-clinic-text-secondary mt-1 block">
            {kpis.completed_today} Completed Encounters
          </span>
        </div>

        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Historical No-Show Rate</span>
            <XCircle className="h-4 w-4 text-rose-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-clinic-text-primary font-mono">
            {kpis.no_show_rate}%
          </div>
          <span className="text-[11px] text-emerald-600 mt-1 block font-medium">
            &bull; Managed by 24h SES Reminders
          </span>
        </div>

        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Avg Triage Wait Time</span>
            <Clock className="h-4 w-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-blue-600 font-mono">
            {kpis.average_wait_time_minutes} min
          </div>
          <span className="text-[11px] text-clinic-text-secondary mt-1 block">
            Check-In to Vitals Intake
          </span>
        </div>
      </div>

      {/* Charts and Distributions Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Doctor Workload Distribution (7 cols) */}
        <div className="lg:col-span-7 rounded-xl border border-clinic-border bg-clinic-surface p-5 shadow-clinical">
          <div className="border-b border-clinic-border pb-3 mb-4 flex items-center justify-between">
            <h2 className="text-sm font-bold text-clinic-text-primary flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-clinic-primary" />
              Physician Consultation Load & Capacity Utilization
            </h2>
            <span className="text-xs text-clinic-text-secondary font-mono">
              Daily Standard: 12 Slots
            </span>
          </div>

          <div className="space-y-4">
            {kpis.doctor_workloads.map((doc) => (
              <div key={doc.doctor_id} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-clinic-text-primary">
                    Dr. {doc.doctor_name} &bull;{" "}
                    <span className="font-normal text-clinic-text-secondary">
                      {doc.specialty}
                    </span>
                  </span>
                  <span className="font-mono text-clinic-text-secondary font-semibold">
                    {doc.total_appointments} visits ({doc.utilization_rate}%)
                  </span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-clinic-canvas border border-clinic-border overflow-hidden">
                  <div
                    className="h-full bg-clinic-primary rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(doc.utilization_rate, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Insurance Status Breakdown (5 cols) */}
        <div className="lg:col-span-5 rounded-xl border border-clinic-border bg-clinic-surface p-5 shadow-clinical">
          <div className="border-b border-clinic-border pb-3 mb-4">
            <h2 className="text-sm font-bold text-clinic-text-primary flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-clinic-primary" />
              Insurance Eligibility Status Distribution
            </h2>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50/60 p-3 text-xs">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-700" />
                <span className="font-bold text-emerald-900">Verified Coverage</span>
              </div>
              <span className="font-mono font-bold text-emerald-800 text-sm">
                {kpis.insurance_breakdown.verified} Patients
              </span>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50/60 p-3 text-xs">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-700" />
                <span className="font-bold text-amber-900">Pending Verification</span>
              </div>
              <span className="font-mono font-bold text-amber-800 text-sm">
                {kpis.insurance_breakdown.pending} Patients
              </span>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-rose-200 bg-rose-50/60 p-3 text-xs">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-rose-700" />
                <span className="font-bold text-rose-900">Self-Pay / Uninsured</span>
              </div>
              <span className="font-mono font-bold text-rose-800 text-sm">
                {kpis.insurance_breakdown.uninsured} Patients
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Volume Time Series Table */}
      <div className="rounded-xl border border-clinic-border bg-clinic-surface overflow-hidden shadow-clinical">
        <div className="border-b border-clinic-border px-5 py-3.5">
          <h2 className="text-sm font-bold text-clinic-text-primary">
            Recent 7-Day Appointment Volume
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-clinic-border bg-clinic-canvas text-clinic-text-secondary uppercase text-[10px] font-semibold">
              <tr>
                <th className="px-5 py-3">Calendar Date</th>
                <th className="px-5 py-3">Total Appointments Scheduled</th>
                <th className="px-5 py-3">Completed Consultations</th>
                <th className="px-5 py-3">Completion Ratio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-clinic-border bg-clinic-canvas">
              {kpis.recent_volume.map((item, idx) => {
                const ratio = item.total > 0 ? Math.round((item.completed / item.total) * 100) : 100;
                return (
                  <tr key={idx} className="hover:bg-clinic-surface">
                    <td className="px-5 py-3 font-semibold text-clinic-text-primary font-mono">
                      {item.date}
                    </td>
                    <td className="px-5 py-3 font-mono text-clinic-text-secondary">
                      {item.total} visits
                    </td>
                    <td className="px-5 py-3 font-mono text-emerald-600 font-semibold">
                      {item.completed} completed
                    </td>
                    <td className="px-5 py-3 font-mono text-clinic-text-secondary">
                      {ratio}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
