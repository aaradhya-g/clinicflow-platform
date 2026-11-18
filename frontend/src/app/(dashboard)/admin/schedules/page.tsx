"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { DoctorProfile, User } from "@/types";
import { Clock, Stethoscope, UserCheck, CheckCircle2, XCircle } from "lucide-react";

export default function AdminSchedulesPage() {
  const queryClient = useQueryClient();

  // Fetch doctors
  const { data: doctors = [], isLoading } = useQuery<DoctorProfile[]>({
    queryKey: ["adminDoctors"],
    queryFn: async () => {
      const res = await apiClient.get<DoctorProfile[]>("/users/doctors");
      return res.data;
    },
  });

  // Fetch staff
  const { data: staff = [] } = useQuery<User[]>({
    queryKey: ["clinicStaff"],
    queryFn: async () => {
      const res = await apiClient.get<User[]>("/users/staff");
      return res.data;
    },
  });

  // Toggle availability mutation
  const toggleMutation = useMutation({
    mutationFn: async ({ id, isAvailable }: { id: string; isAvailable: boolean }) => {
      await apiClient.patch(`/users/doctors/${id}/availability?is_available=${isAvailable}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminDoctors"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to update availability");
    },
  });

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-clinic-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary flex items-center gap-2">
            <Clock className="h-5 w-5 text-clinic-primary" />
            Physician Rosters & Staff Roster Management
          </h1>
          <p className="text-xs text-clinic-text-secondary mt-0.5">
            Configure physician room assignments, daily consultation availability, and staff directory
          </p>
        </div>
      </div>

      {/* Doctor Cards */}
      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-clinic-text-secondary mb-3 flex items-center gap-1.5">
          <Stethoscope className="h-4 w-4 text-clinic-primary" />
          Active Physician Schedules
        </h2>

        {isLoading ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            Loading doctor profiles...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {doctors.map((doc) => (
              <div
                key={doc.id}
                className="rounded-xl border border-clinic-border bg-clinic-surface p-5 shadow-clinical flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-bold text-clinic-text-primary">
                        Dr. {doc.full_name}
                      </h3>
                      <span className="text-xs text-clinic-primary font-semibold">
                        {doc.specialty}
                      </span>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${
                        doc.is_available
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}
                    >
                      {doc.is_available ? "Accepting Patients" : "Unavailable"}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs border-t border-clinic-border pt-3">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-clinic-text-secondary block">
                        Clinic Room Suite
                      </span>
                      <span className="font-medium text-clinic-text-primary">{doc.room_number}</span>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-semibold text-clinic-text-secondary block">
                        Medical License
                      </span>
                      <span className="font-mono text-clinic-text-primary">{doc.license_number}</span>
                    </div>

                    <div className="mt-1">
                      <span className="text-[10px] uppercase font-semibold text-clinic-text-secondary block">
                        Consultation Fee
                      </span>
                      <span className="font-mono font-bold text-clinic-text-primary">
                        ${doc.consultation_fee.toFixed(2)}
                      </span>
                    </div>

                    <div className="mt-1">
                      <span className="text-[10px] uppercase font-semibold text-clinic-text-secondary block">
                        Roster Hours
                      </span>
                      <span className="text-clinic-text-secondary">09:00 AM - 04:30 PM</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-clinic-border flex justify-end">
                  <button
                    onClick={() =>
                      toggleMutation.mutate({
                        id: doc.id,
                        isAvailable: !doc.is_available,
                      })
                    }
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      doc.is_available
                        ? "border border-clinic-border bg-clinic-canvas text-clinic-text-secondary hover:bg-clinic-accent-subtle"
                        : "bg-clinic-primary text-white hover:bg-clinic-primary-hover shadow-clinical"
                    }`}
                  >
                    {doc.is_available ? "Mark as Away / On Leave" : "Set Available for Scheduling"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Staff Directory Table */}
      <div className="rounded-xl border border-clinic-border bg-clinic-surface overflow-hidden shadow-clinical">
        <div className="border-b border-clinic-border px-5 py-3.5 flex items-center justify-between">
          <h2 className="text-sm font-bold text-clinic-text-primary flex items-center gap-2">
            <UserCheck className="h-4 w-4 text-clinic-primary" />
            Clinic Staff Directory & Access Levels
          </h2>
          <span className="text-xs text-clinic-text-secondary font-mono">
            {staff.length} Active System Users
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-clinic-border bg-clinic-canvas text-clinic-text-secondary uppercase text-[10px] font-semibold">
              <tr>
                <th className="px-5 py-3">Staff Name</th>
                <th className="px-5 py-3">Login Email</th>
                <th className="px-5 py-3">Security Role</th>
                <th className="px-5 py-3">Account Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-clinic-border bg-clinic-canvas">
              {staff.map((u) => (
                <tr key={u.id} className="hover:bg-clinic-surface">
                  <td className="px-5 py-3 font-semibold text-clinic-text-primary">{u.full_name}</td>
                  <td className="px-5 py-3 font-mono text-clinic-text-secondary">{u.email}</td>
                  <td className="px-5 py-3 capitalize font-bold text-clinic-primary">
                    <span className="bg-clinic-accent-subtle px-2 py-0.5 rounded border border-clinic-border text-xs">
                      {u.role}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
