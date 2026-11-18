"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Patient, InsuranceStatus } from "@/types";
import { formatDate, calculateAge, getInsuranceBadgeClass } from "@/lib/formatters";
import { Search, ShieldAlert, CheckCircle, Clock, XCircle, Users, AlertCircle } from "lucide-react";

export default function PatientRegistryPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const { data: patients = [], isLoading } = useQuery<Patient[]>({
    queryKey: ["patients", searchQuery, statusFilter],
    queryFn: async () => {
      let url = `/patients/?limit=100`;
      if (searchQuery) url += `&query=${encodeURIComponent(searchQuery)}`;
      if (statusFilter !== "ALL") url += `&insurance_status=${statusFilter}`;
      const res = await apiClient.get<Patient[]>(url);
      return res.data;
    },
  });

  const updateInsuranceMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: InsuranceStatus }) => {
      await apiClient.patch(`/patients/${id}/insurance`, { insurance_status: status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to update insurance status");
    },
  });

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-clinic-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary flex items-center gap-2">
            <Users className="h-5 w-5 text-clinic-primary" />
            Patient Master Index & Insurance Verification
          </h1>
          <p className="text-xs text-clinic-text-secondary mt-0.5">
            Maintain longitudinal patient demographics and update carrier eligibility in real-time
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-clinic-text-secondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search MRN, Name, Phone, or Email..."
            className="w-full rounded-lg border border-clinic-border bg-clinic-canvas py-2 pl-9 pr-3 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          <span className="text-xs font-semibold text-clinic-text-secondary whitespace-nowrap">
            Status Filter:
          </span>
          {["ALL", "Verified", "Pending", "Uninsured"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                statusFilter === st
                  ? "bg-clinic-primary text-white shadow-xs"
                  : "border border-clinic-border bg-clinic-canvas text-clinic-text-secondary hover:bg-clinic-accent-subtle"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Patients Table */}
      <div className="rounded-xl border border-clinic-border bg-clinic-surface overflow-hidden shadow-clinical">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent mb-2" />
            Loading patient records...
          </div>
        ) : patients.length === 0 ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            No patient records match your search criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-clinic-border bg-clinic-canvas text-clinic-text-secondary uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-5 py-3 font-semibold">MRN</th>
                  <th className="px-5 py-3 font-semibold">Patient Name</th>
                  <th className="px-5 py-3 font-semibold">Age / Gender</th>
                  <th className="px-5 py-3 font-semibold">Contact Details</th>
                  <th className="px-5 py-3 font-semibold">Insurance Carrier & Policy</th>
                  <th className="px-5 py-3 font-semibold">Eligibility Status</th>
                  <th className="px-5 py-3 font-semibold">Allergies & History</th>
                  <th className="px-5 py-3 font-semibold text-right">Quick Verify Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-clinic-border bg-clinic-canvas">
                {patients.map((pat) => {
                  const insBadge = getInsuranceBadgeClass(pat.insurance_status);
                  const allergies = pat.medical_history?.allergies || [];
                  const hasAllergies = allergies.length > 0;

                  return (
                    <tr key={pat.id} className="hover:bg-clinic-surface transition">
                      <td className="px-5 py-3.5 font-mono font-bold text-clinic-text-primary whitespace-nowrap">
                        {pat.mrn}
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-clinic-text-primary">
                        {pat.first_name} {pat.last_name}
                      </td>
                      <td className="px-5 py-3.5 text-clinic-text-secondary">
                        {calculateAge(pat.date_of_birth)} yrs &bull; {pat.gender}
                      </td>
                      <td className="px-5 py-3.5 text-clinic-text-secondary font-mono text-[11px]">
                        <div>{pat.phone}</div>
                        <div className="text-[10px] text-slate-400">{pat.email}</div>
                      </td>
                      <td className="px-5 py-3.5 text-clinic-text-secondary">
                        <div className="font-medium text-clinic-text-primary">
                          {pat.insurance_provider || "Self-Pay"}
                        </div>
                        <div className="font-mono text-[11px] text-slate-400">
                          {pat.insurance_policy_number || "None"}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${insBadge.bg} ${insBadge.text} ${insBadge.border}`}
                        >
                          {pat.insurance_status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        {hasAllergies ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full">
                            <AlertCircle className="h-3 w-3" />
                            {allergies.join(", ")}
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400">NKDA (No Known Allergies)</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-right whitespace-nowrap">
                        <select
                          value={pat.insurance_status}
                          onChange={(e) =>
                            updateInsuranceMutation.mutate({
                              id: pat.id,
                              status: e.target.value as InsuranceStatus,
                            })
                          }
                          className="rounded-lg border border-clinic-border bg-clinic-canvas px-2.5 py-1 text-xs font-semibold text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                        >
                          <option value="Verified">Set Verified</option>
                          <option value="Pending">Set Pending</option>
                          <option value="Uninsured">Set Uninsured</option>
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
