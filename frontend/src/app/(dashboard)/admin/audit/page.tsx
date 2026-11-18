"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AuditLog } from "@/types";
import { formatDate } from "@/lib/formatters";
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle,
  Clock,
  Eye,
  Lock,
  Terminal,
} from "lucide-react";

export default function AuditExplorerPage() {
  const [actionFilter, setActionFilter] = useState<string>("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const { data: logs = [], isLoading } = useQuery<AuditLog[]>({
    queryKey: ["auditLogs", actionFilter, roleFilter],
    queryFn: async () => {
      let url = "/audit/?limit=100";
      if (actionFilter) url += `&action=${actionFilter}`;
      if (roleFilter) url += `&role=${roleFilter}`;
      const res = await apiClient.get<AuditLog[]>(url);
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-clinic-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-clinic-primary" />
            Immutable HIPAA Audit Trail Explorer
          </h1>
          <p className="text-xs text-clinic-text-secondary mt-0.5">
            Strict append-only record tracking all access, reads, and modifications to Protected Health Information (PHI)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-clinic-accent-subtle border border-clinic-border px-3 py-1 text-xs font-semibold text-clinic-primary flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5" />
            PostgreSQL Trigger Enforced (Immutable)
          </span>
        </div>
      </div>

      {/* Filter Ribbon */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-clinic-text-secondary" />
          <span className="text-xs font-semibold text-clinic-text-secondary">
            Filter Action:
          </span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
          >
            <option value="">All Audit Actions</option>
            <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
            <option value="REGISTER_PATIENT">REGISTER_PATIENT</option>
            <option value="READ_PATIENT_EHR">READ_PATIENT_EHR</option>
            <option value="CREATE_APPOINTMENT">CREATE_APPOINTMENT</option>
            <option value="RECORD_VITALS">RECORD_VITALS</option>
            <option value="COMPLETE_CONSULTATION">COMPLETE_CONSULTATION</option>
            <option value="UPDATE_INSURANCE_STATUS">UPDATE_INSURANCE_STATUS</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-clinic-text-secondary">
            Filter Role:
          </span>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
          >
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="doctor">Doctor</option>
            <option value="receptionist">Receptionist</option>
          </select>
        </div>

        {(actionFilter || roleFilter) && (
          <button
            onClick={() => {
              setActionFilter("");
              setRoleFilter("");
            }}
            className="text-xs font-semibold text-clinic-primary hover:underline ml-auto"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Audit Log Table */}
      <div className="rounded-xl border border-clinic-border bg-clinic-surface overflow-hidden shadow-clinical">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent mb-2" />
            Querying immutable audit archive...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            No audit log entries found matching criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-clinic-border bg-clinic-canvas text-clinic-text-secondary uppercase text-[10px] font-semibold">
                <tr>
                  <th className="px-5 py-3">Timestamp (UTC)</th>
                  <th className="px-5 py-3">Action</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Target Resource</th>
                  <th className="px-5 py-3">Resource ID</th>
                  <th className="px-5 py-3">Client IP</th>
                  <th className="px-5 py-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-clinic-border bg-clinic-canvas">
                {logs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  return (
                    <tr key={log.id} className="hover:bg-clinic-surface transition">
                      <td className="px-5 py-3 font-mono text-[11px] text-clinic-text-secondary whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString("en-US", {
                          timeZone: "UTC",
                          hour12: false,
                        })}{" "}
                        UTC
                      </td>
                      <td className="px-5 py-3 whitespace-nowrap">
                        <span className="font-mono text-xs font-bold text-clinic-primary bg-clinic-accent-subtle px-2 py-0.5 rounded border border-clinic-border">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-5 py-3 capitalize font-medium text-clinic-text-primary">
                        {log.role}
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px] text-clinic-text-secondary">
                        {log.resource_type}
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px] text-clinic-text-primary max-w-xs truncate" title={log.resource_id}>
                        {log.resource_id}
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px] text-clinic-text-secondary">
                        {log.ip_address}
                      </td>
                      <td className="px-5 py-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                          className="rounded border border-clinic-border bg-clinic-canvas px-2.5 py-1 text-[11px] font-semibold text-clinic-primary hover:bg-clinic-accent-subtle transition"
                        >
                          {isExpanded ? "Hide Diff" : "Inspect"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Expanded JSON Inspector Modal / Card */}
      {expandedLogId && (
        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-clinic-border">
            <span className="text-xs font-bold uppercase tracking-wider text-clinic-text-primary flex items-center gap-1.5">
              <Terminal className="h-4 w-4 text-clinic-primary" />
              Event JSON Metadata Diff &bull; Event ID: {expandedLogId}
            </span>
            <button
              onClick={() => setExpandedLogId(null)}
              className="text-xs font-semibold text-clinic-primary hover:underline"
            >
              Close Inspector
            </button>
          </div>
          <pre className="rounded-lg border border-clinic-border bg-clinic-canvas p-3 font-mono text-xs text-clinic-text-primary overflow-x-auto leading-relaxed">
            {JSON.stringify(
              logs.find((l) => l.id === expandedLogId)?.details || {},
              null,
              2
            )}
          </pre>
        </div>
      )}
    </div>
  );
}
