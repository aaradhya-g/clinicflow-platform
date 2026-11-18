export function formatDate(dateStr: string): string {
  if (!dateStr) return "N/A";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function formatTime(timeStr: string): string {
  if (!timeStr) return "";
  const parts = timeStr.split(":");
  if (parts.length >= 2) {
    let hour = parseInt(parts[0], 10);
    const minute = parts[1];
    const ampm = hour >= 12 ? "PM" : "AM";
    hour = hour % 12 || 12;
    return `${hour}:${minute} ${ampm}`;
  }
  return timeStr;
}

export function calculateAge(dobStr: string): number {
  if (!dobStr) return 0;
  const birth = new Date(dobStr);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const m = now.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}

export function getInsuranceBadgeClass(status?: string): { bg: string; text: string; border: string } {
  switch (status) {
    case "Verified":
      return { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" };
    case "Pending":
      return { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" };
    case "Uninsured":
      return { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200" };
    default:
      return { bg: "bg-slate-50", text: "text-slate-600", border: "border-slate-200" };
  }
}

export function getAppointmentStatusBadge(status: string): { bg: string; text: string; dot: string } {
  switch (status) {
    case "Checked-In":
      return { bg: "bg-emerald-50 text-emerald-800 border-emerald-200", text: "Checked-In", dot: "bg-emerald-500" };
    case "In-Consultation":
      return { bg: "bg-blue-50 text-blue-800 border-blue-200", text: "In-Consultation", dot: "bg-blue-500" };
    case "Scheduled":
      return { bg: "bg-amber-50 text-amber-800 border-amber-200", text: "Scheduled", dot: "bg-amber-500" };
    case "Completed":
      return { bg: "bg-purple-50 text-purple-800 border-purple-200", text: "Completed", dot: "bg-purple-500" };
    case "Cancelled":
    case "No-Show":
      return { bg: "bg-rose-50 text-rose-800 border-rose-200", text: status, dot: "bg-rose-500" };
    default:
      return { bg: "bg-slate-50 text-slate-700 border-slate-200", text: status, dot: "bg-slate-400" };
  }
}

export function getVitalsAlertLevel(vitals: { systolic_bp: number; diastolic_bp: number; spo2_percentage: number; heart_rate: number }): {
  isCritical: boolean;
  message?: string;
} {
  if (vitals.systolic_bp >= 160 || vitals.diastolic_bp >= 100) {
    return { isCritical: true, message: "Hypertensive Crisis Range" };
  }
  if (vitals.spo2_percentage < 92) {
    return { isCritical: true, message: "Hypoxemia Alert (< 92%)" };
  }
  if (vitals.heart_rate >= 120 || vitals.heart_rate < 50) {
    return { isCritical: true, message: "Abnormal Pulse Rate" };
  }
  return { isCritical: false };
}
