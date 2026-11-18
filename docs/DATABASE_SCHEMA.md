# ClinicFlow Database Schema & Indexing Reference

This document details the PostgreSQL 16 relational data model, indexing decisions, and HIPAA compliance data integrity mechanisms in ClinicFlow.

---

## 1. Relational Entities & Data Dictionary

### 1.1 `users`
Core user identity and authentication credentials.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | UUIDv4 identifier |
| `email` | `VARCHAR(255)` | Unique, Not Null | Unique login address |
| `password_hash` | `VARCHAR(255)` | Not Null | 12-round bcrypt salted hash |
| `full_name` | `VARCHAR(255)` | Not Null | Display name |
| `role` | `VARCHAR(50)` | Not Null | Enum: `admin`, `doctor`, `receptionist` |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE` | Account active state |
| `created_at` | `TIMESTAMPTZ` | Default `NOW()` | Audit creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Default `NOW()` | Audit update timestamp |

### 1.2 `doctor_profiles`
Clinical metadata and department details tied 1:1 to a user with role `doctor`.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | UUIDv4 |
| `user_id` | `UUID` | Unique, FK -> `users.id` (CASCADE) | Linked doctor user account |
| `specialty` | `VARCHAR(100)` | Not Null | e.g. Cardiology, Pediatrics |
| `license_number` | `VARCHAR(100)` | Unique, Not Null | Medical Board License ID |
| `room_number` | `VARCHAR(50)` | Not Null | Primary consultation suite |
| `consultation_fee` | `NUMERIC(10,2)` | Default `150.00` | Baseline visit charge |
| `is_available` | `BOOLEAN` | Default `TRUE` | Daily roster availability |

### 1.3 `patients`
Patient demographics and insurance coverage.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | UUIDv4 |
| `mrn` | `VARCHAR(50)` | Unique, Not Null | Medical Record Number (`CF-2026-XXXX`) |
| `first_name` | `VARCHAR(100)` | Not Null | Patient given name |
| `last_name` | `VARCHAR(100)` | Not Null | Patient family name |
| `date_of_birth` | `DATE` | Not Null | DOB for age calculation |
| `gender` | `VARCHAR(20)` | Not Null | Female, Male, Other |
| `phone` | `VARCHAR(50)` | Not Null | Primary contact |
| `email` | `VARCHAR(255)` | Not Null | Notification email |
| `address` | `TEXT` | Nullable | Residential address |
| `emergency_contact` | `VARCHAR(255)`| Nullable | Next of kin contact name & phone |
| `insurance_provider` | `VARCHAR(100)`| Nullable | Carrier name |
| `insurance_policy_number` | `VARCHAR(100)`| Nullable | Policy ID |
| `insurance_status` | `VARCHAR(50)` | Default `'Pending'` | Enum: `Verified`, `Pending`, `Uninsured` |

### 1.4 `patient_medical_histories`
Baseline clinical records.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | UUIDv4 |
| `patient_id` | `UUID` | Unique, FK -> `patients.id` | 1:1 baseline history |
| `blood_type` | `VARCHAR(10)` | Nullable | e.g. O+, A-, B+ |
| `allergies` | `JSONB` | Default `'[]'` | List of drug & environmental allergens |
| `chronic_conditions` | `JSONB` | Default `'[]'` | e.g. Hypertension, Type 2 Diabetes |
| `current_medications`| `JSONB` | Default `'[]'` | Active pre-existing prescriptions |
| `surgical_history` | `TEXT` | Nullable | Previous operative procedures |

### 1.5 `appointments`
Calendar bookings and live clinic queue records.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | UUIDv4 |
| `patient_id` | `UUID` | FK -> `patients.id` (RESTRICT) | Patient |
| `doctor_id` | `UUID` | FK -> `doctor_profiles.id` (RESTRICT) | Attending physician |
| `appointment_date` | `DATE` | Not Null | Calendar date |
| `start_time` | `TIME` | Not Null | Slot start time |
| `end_time` | `TIME` | Not Null | Slot end time |
| `status` | `VARCHAR(50)` | Default `'Scheduled'` | Enum: `Scheduled`, `Checked-In`, `In-Consultation`, `Completed`, `Cancelled`, `No-Show` |
| `reason_for_visit` | `TEXT` | Not Null | Chief complaint / intake reason |
| `reminder_sent` | `BOOLEAN` | Default `FALSE` | Flag for SES reminder worker |

### 1.6 `vitals_records`
Initial triage vitals recorded during receptionist or nurse intake.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | UUIDv4 |
| `appointment_id` | `UUID` | Unique, FK -> `appointments.id` | 1:1 linked to visit |
| `patient_id` | `UUID` | FK -> `patients.id` | Patient reference |
| `recorded_by_user_id` | `UUID` | FK -> `users.id` | User who recorded the vitals |
| `systolic_bp` | `INTEGER` | Check `(40 - 260)` | Systolic Blood Pressure (mmHg) |
| `diastolic_bp` | `INTEGER` | Check `(30 - 160)` | Diastolic Blood Pressure (mmHg) |
| `heart_rate` | `INTEGER` | Check `(30 - 240)` | Pulse (BPM) |
| `temperature_c` | `NUMERIC(4,1)` | Check `(30.0 - 45.0)` | Body Temperature (°C) |
| `spo2_percentage` | `INTEGER` | Check `(50 - 100)` | Pulse Oximetry (%) |
| `respiratory_rate` | `INTEGER` | Check `(6 - 60)` | Breaths / min |
| `weight_kg` | `NUMERIC(5,2)` | Nullable | Body weight |
| `height_cm` | `NUMERIC(5,2)` | Nullable | Height |
| `bmi` | `NUMERIC(4,1)` | Nullable | Calculated Body Mass Index |
| `recorded_at` | `TIMESTAMPTZ` | Default `NOW()` | Timestamp of intake |

### 1.7 `clinical_consultations` & `prescriptions`
Doctor SOAP notes, diagnoses, and structured prescriptions.
- `clinical_consultations`: Linked 1:1 to appointment, contains `chief_complaint`, `clinical_notes`, `diagnosis_codes` (ICD-10 style array), and `follow_up_date`.
- `prescriptions`: Multiple medications per consultation (`medication_name`, `dosage`, `frequency`, `duration`, `instructions`).

### 1.8 `audit_logs`
Immutable HIPAA audit logging table.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Primary Key |
| `timestamp` | `TIMESTAMPTZ` | Exact UTC time of operation |
| `user_id` | `UUID` | Initiating user identifier |
| `role` | `VARCHAR(50)` | Role at time of access |
| `action` | `VARCHAR(50)` | `READ`, `CREATE`, `UPDATE`, `DELETE`, `LOGIN`, `EXPORT` |
| `resource_type`| `VARCHAR(50)` | `PATIENT`, `APPOINTMENT`, `VITALS`, `CONSULTATION`, `PRESCRIPTION` |
| `resource_id` | `VARCHAR(255)`| Identifier of accessed resource |
| `ip_address` | `VARCHAR(50)` | Client IP address |
| `details` | `JSONB` | Metadata / change diff summary |

---

## 2. PostgreSQL Indexes

```sql
-- Double-booking prevention index
CREATE UNIQUE INDEX uq_doctor_slot_active
ON appointments (doctor_id, appointment_date, start_time)
WHERE status NOT IN ('Cancelled', 'No-Show');

-- Doctor calendar lookups
CREATE INDEX idx_appointments_doctor_date
ON appointments (doctor_id, appointment_date);

-- Patient historical lookups
CREATE INDEX idx_appointments_patient_id
ON appointments (patient_id);

-- Receptionist live queue board
CREATE INDEX idx_appointments_date_status
ON appointments (appointment_date, status);

-- 24h Lambda reminder worker index
CREATE INDEX idx_appointments_reminder
ON appointments (appointment_date, reminder_sent)
WHERE status = 'Scheduled' AND reminder_sent = FALSE;

-- Patient MRN fast lookups
CREATE UNIQUE INDEX idx_patients_mrn
ON patients (mrn);

-- Patient Name search
CREATE INDEX idx_patients_name_lookup
ON patients (last_name, first_name);

-- HIPAA Audit Trail chronological scans
CREATE INDEX idx_audit_logs_timestamp
ON audit_logs (timestamp DESC);

-- HIPAA Patient Record investigations
CREATE INDEX idx_audit_logs_resource
ON audit_logs (resource_type, resource_id);
```
