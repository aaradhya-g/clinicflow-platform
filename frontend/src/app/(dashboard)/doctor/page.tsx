"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { Appointment, VitalsRecord } from "@/types";
import { useAuth } from "@/hooks/use-auth";
import {
  formatDate,
  formatTime,
  calculateAge,
  getInsuranceBadgeClass,
  getAppointmentStatusBadge,
} from "@/lib/formatters";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock,
  HeartPulse,
  Stethoscope,
  UserCheck,
  AlertTriangle,
} from "lucide-react";

export default function DoctorQueuePage() {
  const router = useRouter();
  const { user } = useAuth();
  const todayStr = new Date().toISOString().split("T")[0];

  const { data: queue = [], isLoading } = useQuery<Appointment[]>({
    queryKey: ["doctorTodayQueue"],
    queryFn: async () => {
      const res = await apiClient.get<Appointment[]>("/queue/today/doctor");
      return res.data;
    },
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-clinic-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-clinic-primary" />
            Physician Daily Queue & Triage Summary
          </h1>
          <p className="text-xs text-clinic-text-secondary mt-0.5">
            Today&apos;s assigned patient encounters with triage vitals available upfront
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-clinic-accent-subtle border border-clinic-border px-3 py-1 text-xs font-semibold text-clinic-primary">
            Today: {formatDate(todayStr)}
          </span>
        </div>
      </div>

      {/* Queue Patient Cards Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-xs text-clinic-text-secondary">
          <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent mb-2" />
          Loading assigned queue...
        </div>
      ) : queue.length === 0 ? (
        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-12 text-center shadow-clinical">
          <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600 mb-2" />
          <h3 className="text-sm font-bold text-clinic-text-primary">
            No Active Patients in Queue
          </h3>
          <p className="text-xs text-clinic-text-secondary mt-1 max-w-sm mx-auto">
            You currently have no scheduled or waiting patients for today. Check in with reception or view patient history.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {queue.map((apt) => {
            const statusBadge = getAppointmentStatusBadge(apt.status);
            const insBadge = getInsuranceBadgeClass(apt.insurance_status);
            const isReadyForConsultation = apt.status === "Checked-In" || apt.status === "In-Consultation";

            return (
              <div
                key={apt.id}
                className="rounded-xl border border-clinic-border bg-clinic-surface p-5 shadow-clinical transition hover:border-clinic-primary"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-clinic-border pb-4">
                  {/* Left: Patient Name, MRN, Time */}
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-clinic-border bg-clinic-canvas text-clinic-primary font-bold">
                      <HeartPulse className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-clinic-text-primary">
                          {apt.patient_name}
                        </span>
                        <span className="font-mono text-xs font-semibold text-clinic-text-secondary bg-clinic-accent-subtle px-2 py-0.5 rounded border border-clinic-border">
                          {apt.patient_mrn}
                        </span>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border ${insBadge.bg} ${insBadge.text} ${insBadge.border}`}
                        >
                          {apt.insurance_status}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-clinic-text-secondary">
                        <span className="flex items-center gap-1 font-mono font-medium">
                          <Clock className="h-3.5 w-3.5 text-clinic-primary" />
                          {formatTime(apt.start_time)} - {formatTime(apt.end_time)}
                        </span>
                        <span>&bull;</span>
                        <span>
                          {apt.patient_gender} &bull; {apt.patient_dob ? `${calculateAge(apt.patient_dob)} yrs` : "Adult"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Status and Consultation Launcher */}
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border ${statusBadge.bg}`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${statusBadge.dot}`} />
                      {statusBadge.text}
                    </span>

                    <button
                      onClick={() => router.push(`/doctor/consultations/${apt.id}`)}
                      className="flex items-center gap-1.5 rounded-lg bg-clinic-primary px-3.5 py-2 text-xs font-semibold text-white hover:bg-clinic-primary-hover shadow-clinical transition"
                    >
                      <span>
                        {apt.status === "In-Consultation"
                          ? "Resume Consultation"
                          : apt.status === "Completed"
                          ? "View Completed Notes"
                          : "Start Consultation"}
                      </span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Bottom: Chief Complaint & Vitals Summary */}
                <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="flex-1">
                    <span className="font-semibold text-clinic-text-secondary uppercase tracking-wider text-[10px] block">
                      Chief Complaint / Triage Intake Reason
                    </span>
                    <p className="mt-0.5 font-medium text-clinic-text-primary">
                      {apt.reason_for_visit}
                    </p>
                  </div>

                  {/* Vitals summary indicator */}
                  <div className="sm:text-right shrink-0">
                    <span className="font-semibold text-clinic-text-secondary uppercase tracking-wider text-[10px] block">
                      Vitals Status
                    </span>
                    {apt.has_vitals ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 mt-0.5">
                        <CheckCircle2 className="h-4 w-4" />
                        Vitals Recorded Upfront
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 mt-0.5">
                        <Clock className="h-4 w-4" />
                        Pending Reception Triage
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
