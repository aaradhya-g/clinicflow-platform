"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Appointment, VitalsRecord, Prescription } from "@/types";
import {
  formatDate,
  formatTime,
  calculateAge,
  getInsuranceBadgeClass,
  getVitalsAlertLevel,
} from "@/lib/formatters";
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  HeartPulse,
  History,
  Pill,
  Plus,
  Stethoscope,
  Trash2,
  User,
} from "lucide-react";

export default function ConsultationStudioPage() {
  const { id: appointmentId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Consultation Form State
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [soapNotes, setSoapNotes] = useState(
    "SUBJECTIVE:\nPatient presents with...\n\nOBJECTIVE:\nGeneral appearance: Alert and oriented.\nCardiovascular: Regular rate and rhythm.\nRespiratory: Clear to auscultation.\n\nASSESSMENT:\n\nPLAN:\n"
  );
  const [diagnosisList, setDiagnosisList] = useState<Array<{ code: string; name: string }>>([
    { code: "I10", name: "Essential (primary) hypertension" },
  ]);
  const [newDiagCode, setNewDiagCode] = useState("");
  const [newDiagName, setNewDiagName] = useState("");

  // Prescriptions Form State
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [medName, setMedName] = useState("");
  const [dosage, setDosage] = useState("10mg");
  const [frequency, setFrequency] = useState("Once daily in morning");
  const [duration, setDuration] = useState("30 days");
  const [instructions, setInstructions] = useState("Take with water after breakfast.");

  const [formError, setFormError] = useState<string | null>(null);

  // 1. Fetch appointment details
  const { data: appointments = [] } = useQuery<Appointment[]>({
    queryKey: ["appointmentDetail", appointmentId],
    queryFn: async () => {
      const res = await apiClient.get<Appointment[]>(`/appointments/`);
      return res.data;
    },
  });
  const appointment = appointments.find((a) => a.id === appointmentId);

  // 2. Fetch vitals for this appointment
  const { data: vitals } = useQuery<VitalsRecord | null>({
    queryKey: ["appointmentVitals", appointmentId],
    queryFn: async () => {
      if (!appointmentId) return null;
      try {
        const res = await apiClient.get<VitalsRecord>(`/queue/vitals/${appointmentId}`);
        return res.data;
      } catch {
        return null;
      }
    },
    enabled: !!appointmentId,
  });

  // 3. Fetch patient EHR timeline
  const { data: ehrData, isLoading: isEhrLoading } = useQuery<any>({
    queryKey: ["ehrTimeline", appointment?.patient_id],
    queryFn: async () => {
      if (!appointment?.patient_id) return null;
      const res = await apiClient.get(`/consultations/patient/${appointment.patient_id}/timeline`);
      return res.data;
    },
    enabled: !!appointment?.patient_id,
  });

  // Mutation: Submit Consultation
  const submitConsultationMutation = useMutation({
    mutationFn: async () => {
      if (!appointment) return;
      await apiClient.post("/consultations/", {
        appointment_id: appointment.id,
        patient_id: appointment.patient_id,
        chief_complaint: chiefComplaint || appointment.reason_for_visit,
        clinical_notes: soapNotes,
        diagnosis_codes: diagnosisList,
        prescriptions: prescriptions,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctorTodayQueue"] });
      alert("Consultation signed and completed successfully. Records archived.");
      router.push("/doctor");
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || "Failed to submit clinical consultation.");
    },
  });

  // Add prescription helper
  const handleAddPrescription = () => {
    if (!medName.trim()) return;
    setPrescriptions([
      ...prescriptions,
      {
        medication_name: medName.trim(),
        dosage: dosage.trim(),
        frequency: frequency.trim(),
        duration: duration.trim(),
        instructions: instructions.trim(),
      },
    ]);
    setMedName("");
  };

  // Add diagnosis helper
  const handleAddDiagnosis = () => {
    if (!newDiagName.trim()) return;
    setDiagnosisList([
      ...diagnosisList,
      {
        code: newDiagCode.trim() || "ICD-10",
        name: newDiagName.trim(),
      },
    ]);
    setNewDiagCode("");
    setNewDiagName("");
  };

  if (!appointment) {
    return (
      <div className="p-12 text-center text-xs text-clinic-text-secondary">
        <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent mb-2" />
        Loading clinical encounter studio...
      </div>
    );
  }

  const insBadge = getInsuranceBadgeClass(appointment.insurance_status);
  const vitalsAlert = vitals ? getVitalsAlertLevel(vitals) : { isCritical: false };
  const allergies = ehrData?.medical_history?.allergies || [];
  const chronicConditions = ehrData?.medical_history?.chronic_conditions || [];

  return (
    <div className="space-y-6">
      {/* Back and Title Navigation */}
      <div className="flex items-center justify-between border-b border-clinic-border pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/doctor")}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-clinic-border bg-clinic-canvas text-clinic-text-secondary hover:border-clinic-primary hover:text-clinic-primary transition"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-clinic-text-primary flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-clinic-primary" />
              Physician Consultation & EHR Studio
            </h1>
            <span className="text-xs text-clinic-text-secondary">
              Active Visit &bull; {formatDate(appointment.appointment_date)} at {formatTime(appointment.start_time)}
            </span>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={() => submitConsultationMutation.mutate()}
          disabled={submitConsultationMutation.isPending}
          className="flex items-center gap-1.5 rounded-lg bg-clinic-primary px-4 py-2 text-xs font-semibold text-white hover:bg-clinic-primary-hover shadow-clinical transition disabled:opacity-50"
        >
          <CheckCircle2 className="h-4 w-4" />
          <span>
            {submitConsultationMutation.isPending
              ? "Signing & Archiving..."
              : "Sign & Conclude Visit"}
          </span>
        </button>
      </div>

      {formError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{formError}</span>
        </div>
      )}

      {/* --- SECTION 1: Patient Banner & Critical Alerts --- */}
      <div className="rounded-xl border border-clinic-border bg-clinic-surface p-5 shadow-clinical">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Patient Core Info */}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-lg font-bold text-clinic-text-primary">
                {appointment.patient_name}
              </span>
              <span className="font-mono text-xs font-bold text-clinic-primary bg-clinic-accent-subtle px-2 py-0.5 rounded border border-clinic-border">
                {appointment.patient_mrn}
              </span>
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border ${insBadge.bg} ${insBadge.text} ${insBadge.border}`}
              >
                {appointment.insurance_status}
              </span>
            </div>
            <div className="mt-1 flex items-center gap-3 text-xs text-clinic-text-secondary font-medium">
              <span>{appointment.patient_gender}</span>
              <span>&bull;</span>
              <span>{appointment.patient_dob ? `${calculateAge(appointment.patient_dob)} years old` : "Adult"}</span>
              <span>&bull;</span>
              <span>Blood Group: {ehrData?.medical_history?.blood_type || "Unknown"}</span>
            </div>
          </div>

          {/* Allergy & Chronic Condition Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            {allergies.length > 0 ? (
              <div className="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>Allergies: {allergies.join(", ")}</span>
              </div>
            ) : (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                No Known Drug Allergies
              </div>
            )}

            {chronicConditions.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
                Chronic: {chronicConditions.join(", ")}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* --- SECTION 2: Vitals Card & Alert Bar --- */}
      {vitals && (
        <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-clinic-border">
            <span className="text-xs font-bold uppercase tracking-wider text-clinic-text-secondary flex items-center gap-1.5">
              <HeartPulse className="h-4 w-4 text-clinic-primary" />
              Triage Intake Vital Signs (Today)
            </span>
            {vitalsAlert.isCritical && (
              <span className="flex items-center gap-1 text-[11px] font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full">
                <AlertCircle className="h-3.5 w-3.5" />
                {vitalsAlert.message}
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <div className="rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center">
              <span className="text-[10px] text-clinic-text-secondary uppercase font-semibold block">Blood Pressure</span>
              <span className="text-base font-bold font-mono text-clinic-text-primary">
                {vitals.systolic_bp}/{vitals.diastolic_bp}
              </span>
              <span className="text-[10px] text-slate-400 block">mmHg</span>
            </div>

            <div className="rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center">
              <span className="text-[10px] text-clinic-text-secondary uppercase font-semibold block">Heart Rate</span>
              <span className="text-base font-bold font-mono text-clinic-text-primary">
                {vitals.heart_rate}
              </span>
              <span className="text-[10px] text-slate-400 block">BPM</span>
            </div>

            <div className="rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center">
              <span className="text-[10px] text-clinic-text-secondary uppercase font-semibold block">SpO2 Oxygen</span>
              <span className="text-base font-bold font-mono text-clinic-text-primary">
                {vitals.spo2_percentage}%
              </span>
              <span className="text-[10px] text-slate-400 block">Pulse Oximetry</span>
            </div>

            <div className="rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center">
              <span className="text-[10px] text-clinic-text-secondary uppercase font-semibold block">Temperature</span>
              <span className="text-base font-bold font-mono text-clinic-text-primary">
                {vitals.temperature_c}&deg;C
              </span>
              <span className="text-[10px] text-slate-400 block">Body Temp</span>
            </div>

            <div className="rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center">
              <span className="text-[10px] text-clinic-text-secondary uppercase font-semibold block">Weight</span>
              <span className="text-base font-bold font-mono text-clinic-text-primary">
                {vitals.weight_kg || "--"}
              </span>
              <span className="text-[10px] text-slate-400 block">kg</span>
            </div>

            <div className="rounded-lg border border-clinic-border bg-clinic-canvas p-2.5 text-center">
              <span className="text-[10px] text-clinic-text-secondary uppercase font-semibold block">BMI</span>
              <span className="text-base font-bold font-mono text-clinic-text-primary">
                {vitals.bmi || "--"}
              </span>
              <span className="text-[10px] text-slate-400 block">kg/m&sup2;</span>
            </div>
          </div>
        </div>
      )}

      {/* --- SECTION 3: Main Two-Column Workspace --- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Clinical Notes & Prescription Builder (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Chief Complaint */}
          <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
            <label className="text-xs font-bold text-clinic-text-secondary uppercase tracking-wider block mb-1">
              Chief Complaint / Reason for Visit
            </label>
            <input
              type="text"
              value={chiefComplaint || appointment.reason_for_visit}
              onChange={(e) => setChiefComplaint(e.target.value)}
              className="w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3.5 py-2 text-xs font-medium text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
            />
          </div>

          {/* Clinical SOAP Notes Editor */}
          <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-clinic-border">
              <label className="text-xs font-bold text-clinic-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-clinic-primary" />
                Physician SOAP Notes (Subjective, Objective, Assessment, Plan)
              </label>
              <span className="text-[11px] text-slate-400 font-mono">HIPAA Encrypted</span>
            </div>
            <textarea
              rows={9}
              value={soapNotes}
              onChange={(e) => setSoapNotes(e.target.value)}
              className="w-full rounded-lg border border-clinic-border bg-clinic-canvas p-3 font-mono text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none leading-relaxed"
            />
          </div>

          {/* ICD-10 Diagnosis Codes */}
          <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-clinic-border">
              <span className="text-xs font-bold text-clinic-text-secondary uppercase tracking-wider">
                ICD-10 Diagnostic Codes
              </span>
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
              {diagnosisList.map((d, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1 text-xs font-medium text-clinic-text-primary"
                >
                  <span className="font-mono font-bold text-clinic-primary">{d.code}</span>
                  <span>{d.name}</span>
                  <button
                    type="button"
                    onClick={() => setDiagnosisList(diagnosisList.filter((_, i) => i !== idx))}
                    className="text-slate-400 hover:text-rose-600"
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="ICD Code (e.g. I10)"
                value={newDiagCode}
                onChange={(e) => setNewDiagCode(e.target.value)}
                className="w-28 rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs font-mono text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
              />
              <input
                type="text"
                placeholder="Condition description..."
                value={newDiagName}
                onChange={(e) => setNewDiagName(e.target.value)}
                className="flex-1 rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
              />
              <button
                type="button"
                onClick={handleAddDiagnosis}
                className="rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs font-semibold text-clinic-primary hover:bg-clinic-accent-subtle"
              >
                Add Diagnosis
              </button>
            </div>
          </div>

          {/* Structured Prescription Builder */}
          <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-clinic-border">
              <span className="text-xs font-bold text-clinic-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                <Pill className="h-4 w-4 text-clinic-primary" />
                Structured Prescription Studio
              </span>
              <span className="text-[11px] font-mono text-clinic-text-secondary">
                {prescriptions.length} Medications Added
              </span>
            </div>

            {/* Prescriptions List Table */}
            {prescriptions.length > 0 && (
              <div className="mb-4 overflow-hidden rounded-lg border border-clinic-border bg-clinic-canvas">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-clinic-border bg-clinic-surface text-[10px] text-clinic-text-secondary uppercase font-semibold">
                    <tr>
                      <th className="px-3 py-2">Medication</th>
                      <th className="px-3 py-2">Dosage</th>
                      <th className="px-3 py-2">Frequency</th>
                      <th className="px-3 py-2">Duration</th>
                      <th className="px-3 py-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-clinic-border">
                    {prescriptions.map((rx, idx) => (
                      <tr key={idx} className="hover:bg-clinic-surface">
                        <td className="px-3 py-2 font-bold text-clinic-text-primary">{rx.medication_name}</td>
                        <td className="px-3 py-2 font-mono text-clinic-text-secondary">{rx.dosage}</td>
                        <td className="px-3 py-2 text-clinic-text-secondary">{rx.frequency}</td>
                        <td className="px-3 py-2 text-clinic-text-secondary">{rx.duration}</td>
                        <td className="px-3 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setPrescriptions(prescriptions.filter((_, i) => i !== idx))}
                            className="text-slate-400 hover:text-rose-600"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Medication Entry Form */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="col-span-2">
                <label className="text-[10px] font-semibold text-clinic-text-secondary block">Medication Name</label>
                <input
                  type="text"
                  placeholder="e.g. Lisinopril, Metformin, Amoxicillin"
                  value={medName}
                  onChange={(e) => setMedName(e.target.value)}
                  className="mt-0.5 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold text-clinic-text-secondary block">Dosage</label>
                <input
                  type="text"
                  placeholder="e.g. 10mg"
                  value={dosage}
                  onChange={(e) => setDosage(e.target.value)}
                  className="mt-0.5 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold text-clinic-text-secondary block">Duration</label>
                <input
                  type="text"
                  placeholder="e.g. 30 days"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  className="mt-0.5 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div className="col-span-2">
                <label className="text-[10px] font-semibold text-clinic-text-secondary block">Frequency / Schedule</label>
                <input
                  type="text"
                  placeholder="e.g. Once daily in morning"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  className="mt-0.5 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>

              <div className="col-span-2">
                <label className="text-[10px] font-semibold text-clinic-text-secondary block">Instructions to Patient</label>
                <input
                  type="text"
                  placeholder="e.g. Take with food. Do not skip doses."
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  className="mt-0.5 w-full rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs text-clinic-text-primary focus:border-clinic-primary focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={handleAddPrescription}
                className="flex items-center gap-1 rounded-lg border border-clinic-border bg-clinic-canvas px-3 py-1.5 text-xs font-semibold text-clinic-primary hover:bg-clinic-accent-subtle transition"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Medication to Rx
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Patient Longitudinal EHR History Timeline (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-xl border border-clinic-border bg-clinic-surface p-4 shadow-clinical">
            <h3 className="text-xs font-bold text-clinic-text-secondary uppercase tracking-wider flex items-center gap-1.5 pb-2 mb-3 border-b border-clinic-border">
              <History className="h-4 w-4 text-clinic-primary" />
              Patient EHR Timeline & Past Visits
            </h3>

            {isEhrLoading ? (
              <div className="p-6 text-center text-xs text-clinic-text-secondary">
                Loading medical history...
              </div>
            ) : !ehrData?.encounters || ehrData.encounters.length === 0 ? (
              <div className="p-6 text-center text-xs text-clinic-text-secondary">
                No previous recorded encounters on file for this patient.
              </div>
            ) : (
              <div className="space-y-3">
                {ehrData.encounters.map((enc: any) => (
                  <div
                    key={enc.id}
                    className="rounded-lg border border-clinic-border bg-clinic-canvas p-3 text-xs"
                  >
                    <div className="flex items-center justify-between text-[11px] text-clinic-text-secondary font-mono border-b border-clinic-border pb-1 mb-1.5">
                      <span>{formatDate(enc.date)}</span>
                      <span>Dr. {enc.doctor_name}</span>
                    </div>

                    <div className="font-semibold text-clinic-text-primary text-xs">
                      {enc.chief_complaint}
                    </div>

                    {enc.diagnosis_codes?.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {enc.diagnosis_codes.map((dx: any, i: number) => (
                          <span
                            key={i}
                            className="text-[10px] font-mono bg-clinic-accent-subtle border border-clinic-border px-1.5 py-0.5 rounded text-clinic-primary"
                          >
                            {dx.code}: {dx.name}
                          </span>
                        ))}
                      </div>
                    )}

                    {enc.prescriptions?.length > 0 && (
                      <div className="mt-2 text-[11px] text-clinic-text-secondary border-t border-dashed border-clinic-border pt-1.5">
                        <span className="font-semibold text-clinic-text-primary">Prescriptions:</span>{" "}
                        {enc.prescriptions.map((p: any) => p.medication_name).join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
