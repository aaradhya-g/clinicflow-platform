"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Appointment, DoctorProfile, Patient, InsuranceStatus } from "@/types";
import {
  formatDate,
  formatTime,
  calculateAge,
  getInsuranceBadgeClass,
  getAppointmentStatusBadge,
} from "@/lib/formatters";
import {
  Activity,
  CalendarPlus,
  CheckCircle2,
  Clock,
  HeartPulse,
  Plus,
  Search,
  UserCheck,
  UserPlus,
  X,
  AlertTriangle,
} from "lucide-react";

export default function ReceptionistQueuePage() {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

  // Modals state
  const [isVitalsModalOpen, setIsVitalsModalOpen] = useState(false);
  const [selectedAppointmentForVitals, setSelectedAppointmentForVitals] = useState<Appointment | null>(null);

  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

  // Vitals Form State
  const [vitalsForm, setVitalsForm] = useState({
    systolic_bp: 120,
    diastolic_bp: 80,
    heart_rate: 72,
    temperature_c: 36.8,
    spo2_percentage: 98,
    respiratory_rate: 16,
    weight_kg: 70,
    height_cm: 175,
  });
  const [vitalsError, setVitalsError] = useState<string | null>(null);

  // Booking Form State
  const [bookDoctorId, setBookDoctorId] = useState("");
  const [bookPatientId, setBookPatientId] = useState("");
  const [bookDate, setBookDate] = useState(selectedDate);
  const [bookTime, setBookTime] = useState("09:30");
  const [bookReason, setBookReason] = useState("");
  const [bookError, setBookError] = useState<string | null>(null);

  // Patient Registration Form State
  const [regForm, setRegForm] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "1990-01-01",
    gender: "Female",
    phone: "",
    email: "",
    insurance_provider: "",
    insurance_policy_number: "",
    insurance_status: "Verified" as InsuranceStatus,
    allergies: "None",
    chronic_conditions: "None",
  });
  const [regError, setRegError] = useState<string | null>(null);

  // 1. Fetch live queue for selected date
  const { data: queue = [], isLoading: isQueueLoading } = useQuery<Appointment[]>({
    queryKey: ["liveQueue", selectedDate],
    queryFn: async () => {
      const res = await apiClient.get<Appointment[]>(`/queue/live?target_date=${selectedDate}`);
      return res.data;
    },
    refetchInterval: 10000,
  });

  // 2. Fetch doctors for booking dropdown
  const { data: doctors = [] } = useQuery<DoctorProfile[]>({
    queryKey: ["doctors"],
    queryFn: async () => {
      const res = await apiClient.get<DoctorProfile[]>("/users/doctors");
      return res.data;
    },
  });

  // 3. Fetch patients for booking dropdown
  const { data: patientsList = [] } = useQuery<Patient[]>({
    queryKey: ["patientsList"],
    queryFn: async () => {
      const res = await apiClient.get<Patient[]>("/patients/?limit=100");
      return res.data;
    },
  });

  // Mutation: Transition status (Check-in)
  const transitionMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      await apiClient.post(`/queue/${id}/transition`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["liveQueue"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to update queue status");
    },
  });

  // Mutation: Record Vitals
  const recordVitalsMutation = useMutation({
    mutationFn: async () => {
      if (!selectedAppointmentForVitals) return;
      await apiClient.post("/queue/vitals", {
        appointment_id: selectedAppointmentForVitals.id,
        patient_id: selectedAppointmentForVitals.patient_id,
        ...vitalsForm,
      });
    },
    onSuccess: () => {
      setIsVitalsModalOpen(false);
      setSelectedAppointmentForVitals(null);
      queryClient.invalidateQueries({ queryKey: ["liveQueue"] });
    },
    onError: (err: any) => {
      setVitalsError(err.response?.data?.detail || "Failed to record vital signs.");
    },
  });

  // Mutation: Book Appointment
  const bookAppointmentMutation = useMutation({
    mutationFn: async () => {
      const [hour, min] = bookTime.split(":");
      const endHour = (parseInt(hour, 10) + (parseInt(min, 10) === 30 ? 1 : 0)).toString().padStart(2, "0");
      const endMin = parseInt(min, 10) === 30 ? "00" : "30";

      await apiClient.post("/appointments/", {
        patient_id: bookPatientId,
        doctor_id: bookDoctorId,
        appointment_date: bookDate,
        start_time: `${bookTime}:00`,
        end_time: `${endHour}:${endMin}:00`,
        reason_for_visit: bookReason || "General Consultation",
      });
    },
    onSuccess: () => {
      setIsBookModalOpen(false);
      setBookReason("");
      queryClient.invalidateQueries({ queryKey: ["liveQueue"] });
    },
    onError: (err: any) => {
      setBookError(err.response?.data?.detail || "Failed to book appointment.");
    },
  });

  // Mutation: Register Patient
  const registerPatientMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        first_name: regForm.first_name,
        last_name: regForm.last_name,
        date_of_birth: regForm.date_of_birth,
        gender: regForm.gender,
        phone: regForm.phone,
        email: regForm.email,
        insurance_provider: regForm.insurance_provider || null,
        insurance_policy_number: regForm.insurance_policy_number || null,
        insurance_status: regForm.insurance_status,
        medical_history: {
          allergies: regForm.allergies ? regForm.allergies.split(",").map((s) => s.trim()) : [],
          chronic_conditions: regForm.chronic_conditions ? regForm.chronic_conditions.split(",").map((s) => s.trim()) : [],
          current_medications: [],
        },
      };
      const res = await apiClient.post<Patient>("/patients/", payload);
      return res.data;
    },
    onSuccess: (newPatient) => {
      setIsRegisterModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["patientsList"] });
      // Pre-select new patient in booking modal if open
      setBookPatientId(newPatient.id);
    },
    onError: (err: any) => {
      setRegError(err.response?.data?.detail || "Registration failed. Check if email already exists.");
    },
  });

  // Stats calculation
  const totalCount = queue.length;
  const checkedInCount = queue.filter((a) => a.status === "Checked-In").length;
  const inConsultCount = queue.filter((a) => a.status === "In-Consultation").length;
  const completedCount = queue.filter((a) => a.status === "Completed").length;

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-clinic-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary">
            Receptionist Desk & Triage Queue
          </h1>
          <p className="text-xs text-clinic-text-secondary mt-0.5">
            Real-time patient check-in, vital signs intake, and conflict-safe appointment scheduling
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs font-medium text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
          />
          <button
            onClick={() => {
              setRegError(null);
              setIsRegisterModalOpen(true);
            }}
            className="flex items-center gap-1.5 rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-xs font-semibold text-clinic-text-primary hover:border-clinic-primary hover:bg-clinic-accent-subtle transition shadow-xs"
          >
            <UserPlus className="h-4 w-4 text-clinic-primary" />
            <span>New Patient</span>
          </button>
          <button
            onClick={() => {
              setBookError(null);
              if (doctors.length > 0 && !bookDoctorId) setBookDoctorId(doctors[0].id);
              if (patientsList.length > 0 && !bookPatientId) setBookPatientId(patientsList[0].id);
              setIsBookModalOpen(true);
            }}
            className="flex items-center gap-1.5 rounded-lg bg-clinic-primary px-3.5 py-2 text-xs font-semibold text-white hover:bg-clinic-primary-hover transition shadow-clinical"
          >
            <CalendarPlus className="h-4 w-4" />
            <span>Book Appointment</span>
          </button>
        </div>
      </div>

      {/* Metrics Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Scheduled Today</span>
            <Clock className="h-4 w-4" />
          </div>
          <div className="mt-2 text-2xl font-bold text-clinic-text-primary font-mono">
            {totalCount}
          </div>
        </div>

        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Checked-In / In Waiting</span>
            <UserCheck className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600 font-mono">
            {checkedInCount}
          </div>
        </div>

        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">In Consultation</span>
            <Activity className="h-4 w-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-blue-600 font-mono">
            {inConsultCount}
          </div>
        </div>

        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between text-clinic-text-secondary">
            <span className="text-xs font-medium">Completed Visits</span>
            <CheckCircle2 className="h-4 w-4 text-purple-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-purple-600 font-mono">
            {completedCount}
          </div>
        </div>
      </div>

      {/* Live Queue Table Card */}
      <div className="rounded-xl border border-clinic-border bg-clinic-surface overflow-hidden shadow-clinical">
        <div className="border-b border-clinic-border bg-clinic-surface px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h2 className="text-sm font-bold text-clinic-text-primary">
              Live Patient Visit Queue &bull; {formatDate(selectedDate)}
            </h2>
          </div>
          <span className="text-xs text-clinic-text-secondary font-mono">
            {queue.length} Active Records
          </span>
        </div>

        {isQueueLoading ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent mb-2" />
            Refreshing clinic queue...
          </div>
        ) : queue.length === 0 ? (
          <div className="p-12 text-center text-xs text-clinic-text-secondary">
            No appointments scheduled for {formatDate(selectedDate)}. Click &quot;Book Appointment&quot; above to schedule.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-clinic-border bg-clinic-canvas text-clinic-text-secondary uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-5 py-3 font-semibold">Time</th>
                  <th className="px-5 py-3 font-semibold">Patient Demographics</th>
                  <th className="px-5 py-3 font-semibold">Insurance</th>
                  <th className="px-5 py-3 font-semibold">Attending Doctor</th>
                  <th className="px-5 py-3 font-semibold">Reason for Visit</th>
                  <th className="px-5 py-3 font-semibold">Triage Vitals</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-clinic-border bg-clinic-canvas">
                {queue.map((apt) => {
                  const insBadge = getInsuranceBadgeClass(apt.insurance_status);
                  const statusBadge = getAppointmentStatusBadge(apt.status);
                  const isCheckedIn = apt.status === "Checked-In";
                  const isScheduled = apt.status === "Scheduled";

                  return (
                    <tr
                      key={apt.id}
                      className="hover:bg-clinic-surface transition"
                    >
                      {/* Scheduled Time */}
                      <td className="px-5 py-3.5 font-mono font-medium text-clinic-text-primary whitespace-nowrap">
                        {formatTime(apt.start_time)}
                      </td>

                      {/* Patient Info */}
                      <td className="px-5 py-3.5">
                        <div className="font-semibold text-clinic-text-primary">
                          {apt.patient_name}
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-clinic-text-secondary font-mono mt-0.5">
                          <span>{apt.patient_mrn}</span>
                          <span>&bull;</span>
                          <span>{apt.patient_gender}</span>
                          {apt.patient_dob && (
                            <>
                              <span>&bull;</span>
                              <span>{calculateAge(apt.patient_dob)}y</span>
                            </>
                          )}
                        </div>
                      </td>

                      {/* Insurance Status */}
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border ${insBadge.bg} ${insBadge.text} ${insBadge.border}`}
                        >
                          {apt.insurance_status || "Pending"}
                        </span>
                      </td>

                      {/* Doctor & Room */}
                      <td className="px-5 py-3.5">
                        <div className="font-medium text-clinic-text-primary">
                          {apt.doctor_name}
                        </div>
                        <div className="text-[11px] text-clinic-text-secondary">
                          {apt.doctor_specialty} &bull; {apt.room_number}
                        </div>
                      </td>

                      {/* Chief Complaint / Reason */}
                      <td className="px-5 py-3.5 max-w-xs truncate text-clinic-text-secondary" title={apt.reason_for_visit}>
                        {apt.reason_for_visit}
                      </td>

                      {/* Vitals Intake Status */}
                      <td className="px-5 py-3.5">
                        {apt.has_vitals ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                            <HeartPulse className="h-3 w-3" />
                            Recorded
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                            <Clock className="h-3 w-3" />
                            Pending Intake
                          </span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${statusBadge.bg}`}
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${statusBadge.dot}`} />
                          {statusBadge.text}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-3.5 text-right whitespace-nowrap space-x-1.5">
                        {isScheduled && (
                          <button
                            onClick={() =>
                              transitionMutation.mutate({
                                id: apt.id,
                                status: "Checked-In",
                              })
                            }
                            className="rounded border border-clinic-border bg-clinic-surface px-2.5 py-1 text-[11px] font-semibold text-clinic-primary hover:border-clinic-primary hover:bg-clinic-accent-subtle transition"
                          >
                            Check In
                          </button>
                        )}

                        {isCheckedIn && !apt.has_vitals && (
                          <button
                            onClick={() => {
                              setSelectedAppointmentForVitals(apt);
                              setVitalsError(null);
                              setIsVitalsModalOpen(true);
                            }}
                            className="rounded bg-clinic-primary px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-clinic-primary-hover transition"
                          >
                            Record Vitals
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* --- MODAL 1: Triage Vitals Intake --- */}
      {isVitalsModalOpen && selectedAppointmentForVitals && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl border border-clinic-border bg-clinic-surface p-6 shadow-clinical">
            <div className="flex items-center justify-between border-b border-clinic-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-clinic-text-primary flex items-center gap-1.5">
                  <HeartPulse className="h-4 w-4 text-clinic-primary" />
                  Triage Vitals Intake
                </h3>
                <span className="text-xs text-clinic-text-secondary">
                  Patient: {selectedAppointmentForVitals.patient_name} ({selectedAppointmentForVitals.patient_mrn})
                </span>
              </div>
              <button
                onClick={() => setIsVitalsModalOpen(false)}
                className="text-clinic-text-secondary hover:text-clinic-text-primary"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {vitalsError && (
              <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700">
                {vitalsError}
              </div>
            )}

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Systolic BP (mmHg)
                </label>
                <input
                  type="number"
                  value={vitalsForm.systolic_bp}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, systolic_bp: parseInt(e.target.value, 10) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Diastolic BP (mmHg)
                </label>
                <input
                  type="number"
                  value={vitalsForm.diastolic_bp}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, diastolic_bp: parseInt(e.target.value, 10) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Heart Rate (BPM)
                </label>
                <input
                  type="number"
                  value={vitalsForm.heart_rate}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, heart_rate: parseInt(e.target.value, 10) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Temperature (&deg;C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={vitalsForm.temperature_c}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, temperature_c: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  SpO2 Saturation (%)
                </label>
                <input
                  type="number"
                  value={vitalsForm.spo2_percentage}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, spo2_percentage: parseInt(e.target.value, 10) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Respiratory Rate (BPM)
                </label>
                <input
                  type="number"
                  value={vitalsForm.respiratory_rate}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, respiratory_rate: parseInt(e.target.value, 10) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Weight (kg)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={vitalsForm.weight_kg}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, weight_kg: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Height (cm)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={vitalsForm.height_cm}
                  onChange={(e) =>
                    setVitalsForm({ ...vitalsForm, height_cm: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>
            </div>

            {/* Calculated BMI */}
            <div className="mt-3 rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 flex items-center justify-between text-xs">
              <span className="text-clinic-text-secondary font-medium">Computed BMI:</span>
              <span className="font-mono font-bold text-clinic-text-primary">
                {(vitalsForm.weight_kg / Math.pow(vitalsForm.height_cm / 100, 2)).toFixed(1)} kg/m&sup2;
              </span>
            </div>

            <div className="mt-5 flex justify-end gap-2 border-t border-clinic-border pt-4">
              <button
                type="button"
                onClick={() => setIsVitalsModalOpen(false)}
                className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-xs font-semibold text-clinic-text-secondary hover:bg-clinic-accent-subtle"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => recordVitalsMutation.mutate()}
                disabled={recordVitalsMutation.isPending}
                className="rounded-lg bg-clinic-primary px-4 py-2 text-xs font-semibold text-white hover:bg-clinic-primary-hover disabled:opacity-50"
              >
                {recordVitalsMutation.isPending ? "Submitting Vitals..." : "Save Intake Vitals"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL 2: Conflict-Safe Appointment Booking --- */}
      {isBookModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-2xl border border-clinic-border bg-clinic-surface p-6 shadow-clinical">
            <div className="flex items-center justify-between border-b border-clinic-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-clinic-text-primary flex items-center gap-1.5">
                  <CalendarPlus className="h-4 w-4 text-clinic-primary" />
                  Schedule Appointment
                </h3>
                <span className="text-xs text-clinic-text-secondary">
                  Enforces atomic locking to eliminate double-booking
                </span>
              </div>
              <button
                onClick={() => setIsBookModalOpen(false)}
                className="text-clinic-text-secondary hover:text-clinic-text-primary"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {bookError && (
              <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700">
                {bookError}
              </div>
            )}

            <div className="mt-4 space-y-3 text-xs">
              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Select Patient
                </label>
                <select
                  value={bookPatientId}
                  onChange={(e) => setBookPatientId(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                >
                  {patientsList.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.first_name} {p.last_name} ({p.mrn})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Attending Physician
                </label>
                <select
                  value={bookDoctorId}
                  onChange={(e) => setBookDoctorId(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                >
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      Dr. {d.full_name} ({d.specialty} &bull; {d.room_number})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold text-clinic-text-secondary block">
                    Consultation Date
                  </label>
                  <input
                    type="date"
                    value={bookDate}
                    onChange={(e) => setBookDate(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-clinic-text-secondary block">
                    Slot Time
                  </label>
                  <select
                    value={bookTime}
                    onChange={(e) => setBookTime(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                  >
                    <option value="09:00">09:00 AM</option>
                    <option value="09:30">09:30 AM</option>
                    <option value="10:00">10:00 AM</option>
                    <option value="10:30">10:30 AM</option>
                    <option value="11:00">11:00 AM</option>
                    <option value="11:30">11:30 AM</option>
                    <option value="13:30">01:30 PM</option>
                    <option value="14:00">02:00 PM</option>
                    <option value="14:30">02:30 PM</option>
                    <option value="15:00">03:00 PM</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Reason for Visit / Chief Complaint
                </label>
                <textarea
                  rows={2}
                  value={bookReason}
                  onChange={(e) => setBookReason(e.target.value)}
                  placeholder="e.g. Follow-up for episodic heart palpitations..."
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2 border-t border-clinic-border pt-4">
              <button
                type="button"
                onClick={() => setIsBookModalOpen(false)}
                className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-xs font-semibold text-clinic-text-secondary hover:bg-clinic-accent-subtle"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => bookAppointmentMutation.mutate()}
                disabled={bookAppointmentMutation.isPending}
                className="rounded-lg bg-clinic-primary px-4 py-2 text-xs font-semibold text-white hover:bg-clinic-primary-hover disabled:opacity-50"
              >
                {bookAppointmentMutation.isPending ? "Confirming Slot..." : "Confirm Booking"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL 3: New Patient Registration --- */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl border border-clinic-border bg-clinic-surface p-6 shadow-clinical">
            <div className="flex items-center justify-between border-b border-clinic-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-clinic-text-primary flex items-center gap-1.5">
                  <UserPlus className="h-4 w-4 text-clinic-primary" />
                  Register New Patient
                </h3>
                <span className="text-xs text-clinic-text-secondary">
                  Auto-generates sequential MRN (CF-2026-XXXX) & baseline EHR
                </span>
              </div>
              <button
                onClick={() => setIsRegisterModalOpen(false)}
                className="text-clinic-text-secondary hover:text-clinic-text-primary"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {regError && (
              <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700">
                {regError}
              </div>
            )}

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  First Name
                </label>
                <input
                  type="text"
                  required
                  value={regForm.first_name}
                  onChange={(e) => setRegForm({ ...regForm, first_name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Last Name
                </label>
                <input
                  type="text"
                  required
                  value={regForm.last_name}
                  onChange={(e) => setRegForm({ ...regForm, last_name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={regForm.date_of_birth}
                  onChange={(e) => setRegForm({ ...regForm, date_of_birth: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Gender
                </label>
                <select
                  value={regForm.gender}
                  onChange={(e) => setRegForm({ ...regForm, gender: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Contact Phone
                </label>
                <input
                  type="text"
                  placeholder="(555) 000-0000"
                  value={regForm.phone}
                  onChange={(e) => setRegForm({ ...regForm, phone: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="patient@example.com"
                  value={regForm.email}
                  onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Insurance Provider
                </label>
                <input
                  type="text"
                  placeholder="e.g. Blue Cross Blue Shield"
                  value={regForm.insurance_provider}
                  onChange={(e) => setRegForm({ ...regForm, insurance_provider: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-clinic-text-secondary block">
                  Insurance Status
                </label>
                <select
                  value={regForm.insurance_status}
                  onChange={(e) =>
                    setRegForm({ ...regForm, insurance_status: e.target.value as InsuranceStatus })
                  }
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                >
                  <option value="Verified">Verified</option>
                  <option value="Pending">Pending</option>
                  <option value="Uninsured">Uninsured</option>
                </select>
              </div>

              <div className="col-span-2">
                <label className="font-semibold text-clinic-text-secondary block">
                  Known Allergies (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Penicillin, Latex, Peanuts"
                  value={regForm.allergies}
                  onChange={(e) => setRegForm({ ...regForm, allergies: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2 border-t border-clinic-border pt-4">
              <button
                type="button"
                onClick={() => setIsRegisterModalOpen(false)}
                className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-2 text-xs font-semibold text-clinic-text-secondary hover:bg-clinic-accent-subtle"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => registerPatientMutation.mutate()}
                disabled={registerPatientMutation.isPending}
                className="rounded-lg bg-clinic-primary px-4 py-2 text-xs font-semibold text-white hover:bg-clinic-primary-hover disabled:opacity-50"
              >
                {registerPatientMutation.isPending ? "Creating Record..." : "Register Patient"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
