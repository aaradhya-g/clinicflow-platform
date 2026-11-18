# ClinicFlow System Architecture & Engineering Documentation

ClinicFlow is an enterprise-grade medical clinic management, triage queue, and Electronic Health Record (EHR) platform built with a high-reliability, cloud-native architecture.

---

## 1. High-Level Architecture Overview

ClinicFlow is structured into a modern decoupled architecture:
1. **Frontend Presentation Layer:** Next.js (App Router, React 19, TypeScript, Tailwind CSS) deployed on **AWS Amplify Hosting** with Server-Side Rendering (SSR) and edge CDN caching.
2. **Backend API & Business Logic Layer:** FastAPI (Python 3.12) running in a multi-stage containerized environment orchestrated by **Amazon ECS (Fargate)** behind an **Application Load Balancer (ALB)**.
3. **Primary Relational Store:** **Amazon RDS for PostgreSQL 16** (Multi-AZ deployment) with automated daily snapshots, read replicas, and strict relational integrity constraints.
4. **Serverless Asynchronous Event Worker:** **AWS Lambda** triggered by **Amazon EventBridge** cron schedules for dispatching clinical reminders through **Amazon Simple Email Service (SES)**.
5. **Security & Compliance Layer:** End-to-end TLS 1.3 encryption, JWT role-based access control (RBAC), and an immutable database-level HIPAA audit logging trail.

```
                              +-------------------------------------------+
                              |               Client Devices              |
                              |   (Receptionist, Doctor, Admin Desktops)  |
                              +---------------------+---------------------+
                                                    |
                                                    | HTTPS (TLS 1.3)
                                                    v
+------------------------+             +----------------------------------+
|      AWS Amplify       |             |   AWS Application Load Balancer  |
|  (Next.js App Router)  | <---------  |              (ALB)               |
+------------------------+             +-----------------+----------------+
                                                         |
                                                         | HTTP / Internal VPC
                                                         v
                                       +----------------------------------+
                                       |      Amazon ECS (Fargate)        |
                                       |    FastAPI (Python 3.12, Async)  |
                                       |  - JWT RBAC Enforcement          |
                                       |  - Concurrency Lock Engine       |
                                       |  - HIPAA Audit Log Interceptor   |
                                       +-----------------+----------------+
                                                         |
                         +-------------------------------+-------------------------------+
                         |                                                               |
                         v                                                               v
         +-------------------------------+                               +-------------------------------+
         |     Amazon RDS (PostgreSQL)   |                               |      Amazon EventBridge       |
         |  - Multi-AZ High Availability |                               |     (Daily Scheduled Cron)    |
         |  - Partial Unique Indexes     |                               +---------------+---------------+
         |  - Row-Level Locking          |                                               |
         |  - Immutable Audit Triggers   |                                               v
         +---------------+---------------+                               +-------------------------------+
                         ^                                               |       AWS Lambda Worker       |
                         |                                               |   (reminder_worker.py)        |
                         +-----------------------------------------------+   - Queries 24h Bookings      |
                                        Queries Appointments             |   - Dispatches Reminders      |
                                                                         +---------------+---------------+
                                                                                         |
                                                                                         v
                                                                         +-------------------------------+
                                                                         |        Amazon SES             |
                                                                         |   (Patient Email Reminders)   |
                                                                         +-------------------------------+
```

---

## 2. Database Schema & Concurrency Strategy

### 2.1 Schema Design
The relational schema is normalized to 3NF with clinical safety as the highest priority:
- `users`: Identity authentication, bcrypt hashed credentials, and role assignments (`admin`, `doctor`, `receptionist`).
- `doctor_profiles`: Medical specialties, license registration, room assignments, and scheduling configurations.
- `patients`: Demographics, Medical Record Number (`MRN`), contact details, and insurance eligibility statuses (`Verified`, `Pending`, `Uninsured`).
- `patient_medical_histories`: Baseline clinical information including allergies, chronic conditions, current medications, and blood types.
- `appointments`: Booking calendar records with time windows, status state machine, and reminder tracking.
- `vitals_records`: Triage intake values (Systolic/Diastolic BP, Heart Rate, Body Temperature, SpO2, Respiratory Rate, BMI).
- `clinical_consultations`: Doctor SOAP encounter records, chief complaints, diagnostic codes (ICD-10 style), and follow-up orders.
- `prescriptions`: Structured prescription records (medication name, dosage, frequency, duration, special instructions).
- `audit_logs`: Immutable, append-only record tracking all reads, updates, and creation of Protected Health Information (PHI).

### 2.2 Double-Booking Prevention Rationale
In high-throughput clinic operations, two receptionists simultaneously scheduling a patient for the same doctor at the same hour will cause a race condition if not strictly handled at both the application and database tiers:
1. **Application-Level Row Lock (`SELECT ... FOR UPDATE`):**
   Prior to confirming a booking, the API acquires an exclusive pessimistic lock on conflicting slots for that specific doctor and date.
2. **Database-Level Partial Unique Index:**
   ```sql
   CREATE UNIQUE INDEX uq_doctor_slot_active
   ON appointments (doctor_id, appointment_date, start_time)
   WHERE status NOT IN ('Cancelled', 'No-Show');
   ```
   Even if simultaneous requests bypass application boundaries, the database engine enforces atomicity and raises an immediate integrity violation (`409 Conflict`), eliminating double-booking hazards.

### 2.3 Queue Progression State Machine
ClinicFlow enforces a directional state machine for patient visits:
```
[Scheduled]  ──(Patient Arrives)──>  [Checked-In]  ──(Vitals Intaken)──>  [In-Consultation]  ──(Consultation Finished)──>  [Completed]
     │                                     │
     └──(Patient Cancels)──> [Cancelled]   └──(Patient Leaves)──> [No-Show]
```
- A consultation cannot begin without an intake vitals record.
- Prescriptions can only be authored and signed during active or completed consultations by the assigned physician.

---

## 3. HIPAA Security & Compliance Controls

1. **Immutable Audit Logs:**
   The `audit_logs` table has a PostgreSQL trigger (`trg_audit_logs_immutable`) that intercepts and rejects any `UPDATE` or `DELETE` statement, preventing log tampering.
2. **Least Privilege Role-Based Access Control (RBAC):**
   - **Receptionists:** Can register patients, verify insurance, view schedules, and record triage vitals. Cannot view or edit clinical diagnosis notes or prescriptions.
   - **Doctors:** Can access their assigned daily queue, review medical histories, record diagnoses, and issue prescriptions. Cannot modify clinic financial or staff administrative data.
   - **Admins:** Can monitor clinic KPIs, oversee staff schedules, and inspect audit logs. Cannot alter physician clinical judgments.
3. **Session Security:**
   - Stateless signed JWT access tokens with a short 30-minute time-to-live (TTL).
   - Rolling refresh tokens with 7-day TTL stored with strict origin verification.

---

## 4. Serverless Reminder Worker Design

Located in `infra/lambda/reminder_worker.py`:
- Triggered daily (e.g. 08:00 UTC) via Amazon EventBridge Cron.
- Queries `appointments` where:
  - `appointment_date = CURRENT_DATE + INTERVAL '1 day'`
  - `status = 'Scheduled'`
  - `reminder_sent = FALSE`
- Formats a clinical notification with doctor name, room number, scheduled time, and clinic address.
- Dispatches emails via **Amazon SES** using `boto3`.
- In local development, the worker operates in **Mock Mode** (`MOCK_SES=true`), logging formatted emails without making outbound AWS API calls.

---

## 5. AWS Deployment Pipeline & CI/CD

### 5.1 Infrastructure Components
- **AWS Amplify:** Connects to the GitHub repository branch `main`, builds the Next.js frontend, provisions edge lambdas for SSR, and provides managed TLS certificates.
- **Amazon ECR (Elastic Container Registry):** Stores immutable multi-stage Docker images tagged with Git commit SHAs.
- **Amazon ECS (Fargate):** Runs serverless backend containers in private subnets across multiple Availability Zones with auto-scaling based on CPU/Memory metrics.
- **Application Load Balancer (ALB):** Terminates HTTPS and balances requests to healthy backend tasks using the `/healthz` health-check endpoint.

### 5.2 GitHub Actions Pipeline (`.github/workflows/deploy.yml`)
1. **Lint & Test Stage:** Runs Ruff, Mypy, and Pytest (with concurrency and RBAC test suites).
2. **Build Stage:** Builds the backend Docker container using multi-stage caching.
3. **Deploy Stage:** Authenticates with AWS via OIDC or IAM keys, pushes the container to ECR, and triggers an ECS service rolling update.
