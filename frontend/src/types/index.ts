export type UserRole = "admin" | "doctor" | "receptionist";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  doctor_profile?: DoctorProfile;
}

export interface DoctorProfile {
  id: string;
  user_id: string;
  specialty: string;
  license_number: string;
  room_number: string;
  consultation_fee: number;
  is_available: boolean;
  full_name?: string;
  email?: string;
}

export type InsuranceStatus = "Verified" | "Pending" | "Uninsured";

export interface MedicalHistory {
  id?: string;
  patient_id?: string;
  blood_type?: string;
  allergies: string[];
  chronic_conditions: string[];
  current_medications: string[];
  surgical_history?: string;
}

export interface Patient {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  email: string;
  address?: string;
  emergency_contact?: string;
  insurance_provider?: string;
  insurance_policy_number?: string;
  insurance_status: InsuranceStatus;
  medical_history?: MedicalHistory;
  created_at: string;
}

export type AppointmentStatus =
  | "Scheduled"
  | "Checked-In"
  | "In-Consultation"
  | "Completed"
  | "Cancelled"
  | "No-Show";

export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  reason_for_visit: string;
  reminder_sent: boolean;
  created_at: string;
  patient_name?: string;
  patient_mrn?: string;
  patient_gender?: string;
  patient_dob?: string;
  insurance_status?: InsuranceStatus;
  doctor_name?: string;
  doctor_specialty?: string;
  room_number?: string;
  has_vitals: boolean;
  has_consultation: boolean;
}

export interface VitalsRecord {
  id: string;
  appointment_id: string;
  patient_id: string;
  systolic_bp: number;
  diastolic_bp: number;
  heart_rate: number;
  temperature_c: number;
  spo2_percentage: number;
  respiratory_rate?: number;
  weight_kg?: number;
  height_cm?: number;
  bmi?: number;
  recorded_at: string;
}

export interface Prescription {
  id?: string;
  medication_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions?: string;
}

export interface ClinicalConsultation {
  id: string;
  appointment_id: string;
  patient_id: string;
  doctor_id: string;
  chief_complaint: string;
  clinical_notes: string;
  diagnosis_codes: Array<{ code: string; name: string }>;
  follow_up_date?: string;
  created_at: string;
  prescriptions: Prescription[];
}

export interface ClinicKPIs {
  total_patients: number;
  today_appointments: number;
  completed_today: number;
  no_show_rate: number;
  average_wait_time_minutes: number;
  status_breakdown: {
    scheduled: number;
    checked_in: number;
    in_consultation: number;
    completed: number;
    cancelled: number;
    no_show: number;
  };
  insurance_breakdown: {
    verified: number;
    pending: number;
    uninsured: number;
  };
  doctor_workloads: Array<{
    doctor_id: string;
    doctor_name: string;
    specialty: string;
    total_appointments: number;
    completed_appointments: number;
    utilization_rate: number;
  }>;
  recent_volume: Array<{
    date: string;
    total: number;
    completed: number;
  }>;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id?: string;
  role: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
  details: Record<string, any>;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  role: UserRole;
  full_name: string;
}
