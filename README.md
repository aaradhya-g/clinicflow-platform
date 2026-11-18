# ClinicFlow: Enterprise Clinic Appointment, Triage & EHR Platform

ClinicFlow is a production-grade, HIPAA-ready clinical operations system providing atomic scheduling, real-time triage queue management, patient electronic health records (EHR), clinical note-taking with structured prescriptions, and operational analytics.

---

## 1. System Architecture & Tech Stack

- **Frontend:** Next.js (App Router, React 18, TypeScript), Tailwind CSS with a strict clinical palette, Lucide Icons, and TanStack Query. Configured for **AWS Amplify Hosting**.
- **Backend API:** FastAPI (Python 3.12), SQLAlchemy 2.0 (async), Alembic migrations, Pydantic v2, PyJWT + Bcrypt. Containerized for **Amazon ECS (Fargate)**.
- **Relational Store:** PostgreSQL 16 (configured for **AWS RDS Multi-AZ**) with partial unique indexes preventing double-booking and immutable audit log triggers.
- **Serverless Worker:** Standalone **AWS Lambda** worker (`infra/lambda/reminder_worker.py`) triggered by **Amazon EventBridge** cron that queries upcoming 24h appointments and dispatches reminders via **Amazon SES** (plus a local mock mode).
- **CI/CD:** GitHub Actions workflow (`.github/workflows/deploy.yml`) running linting, automated unit/concurrency tests, building Docker containers to **Amazon ECR**, and executing rolling zero-downtime deployments on ECS Fargate.

---

## 2. Strict Visual Design System

ClinicFlow uses a calm, clinical, high-contrast **Pure White & Very Light Rose** palette:

| Token | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Primary Canvas** | `#FFFFFF` | Main application background |
| **Secondary Surface** | `#FFF8F8` | Sidebars, modals, panels, and cards with `1px solid #FCE8E8` borders |
| **Soft Accent / Hover** | `#FFF0F0` | Pill hover, inactive buttons, table rows |
| **Active Pill Fill** | `#FFE4E6` | Active navigation tabs, slot indicators |
| **Primary Brand Action**| `#E11D48` | Primary CTA buttons, clinical markers (hover `#BE123C`) |
| **Primary Typography** | `#1E1B1E` | High contrast headings & clinical body text (WCAG AA+) |
| **Secondary Typography**| `#645D62` | Muted slate labels and timestamps |
| **Semantic Badges** | Emerald (`#ECFDF5`/`#047857`) | Checked-In, Verified coverage |
| | Amber (`#FFFBEB`/`#B45309`) | Scheduled, Pending verification |
| | Rose (`#FFF1F2`/`#BE123C`) | Urgent alerts, Cancelled, Allergies |

---

## 3. Pre-Seeded Demo Credentials

A single command seeds realistic test data across all three security roles:

| Role | Login Email | Password | Primary Workspace Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@clinicflow.med` | `AdminPass123!` | Operational Analytics, HIPAA Audit Log Explorer, Staff Management |
| **Doctor** | `doctor.chen@clinicflow.med` | `DoctorPass123!` | Daily Patient Queue, Upfront Vitals, EHR Studio, SOAP Notes & Prescriptions |
| **Receptionist** | `receptionist@clinicflow.med` | `ReceptionPass123!` | Live Queue Board, Check-in, Triage Vitals Intake, Conflict-Safe Scheduler |

> **Tip:** The unified login screen (`/login`) also features **1-Click Demo Evaluation Pills** to immediately switch roles without manually typing credentials.

---

## 4. Local Development Quickstart

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for full containerization)

### Option A: Local Bare-Metal (Recommended for fast dev)

1. **Backend Setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Seed the database with demo accounts, 4 doctors, 15 patients, and appointments
   python scripts/seed.py
   
   # Start the FastAPI server
   uvicorn app.main:app --reload --port 8000
   ```
   API interactive docs will be available at: `http://localhost:8000/api/v1/docs`

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

### Option B: Docker Compose (Full Stack with PostgreSQL 16)

```bash
docker compose up --build
```
This automatically boots PostgreSQL 16, executes database seeds, starts the FastAPI API on port `8000`, and launches the Next.js frontend on port `3000`.

---

## 5. Automated Testing

ClinicFlow includes comprehensive automated pytest suites validating RBAC permissions, double-booking race condition prevention, and queue triage state machine integrity:

```bash
# Run backend test suite
pytest backend/tests -v

# Run the 24-hour reminder worker in local mock mode
python infra/lambda/reminder_worker.py
```

---

## 6. AWS Production Deployment Architecture

```
                       Internet
                          |
              +-----------+-----------+
              |                       |
              v                       v
      AWS Amplify Hosting     Application Load Balancer
     (Next.js App Router)              (ALB)
                                      |
                                      v
                             Amazon ECS (Fargate)
                          (FastAPI Async Containers)
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
               Amazon RDS (PostgreSQL)    Amazon EventBridge (Cron)
               - Multi-AZ High Availability        |
               - Double-Booking Constraints        v
               - Immutable Audit Triggers  AWS Lambda (reminder_worker)
                                                   |
                                                   v
                                              Amazon SES
                                           (Email Reminders)
```

1. **Frontend on AWS Amplify:** Connect your GitHub repository to AWS Amplify Hosting; it reads `frontend/amplify.yml` to automatically build and deploy SSR Next.js.
2. **Backend on Amazon ECS Fargate:** The GitHub Actions workflow (`.github/workflows/deploy.yml`) builds the multi-stage `Dockerfile`, pushes to **Amazon ECR**, and performs zero-downtime rolling deployments on ECS Fargate.
3. **Database on Amazon RDS:** Provision an RDS PostgreSQL 16 instance. Apply migrations with `alembic upgrade head`.
4. **Serverless Reminders on AWS Lambda:** Package `infra/lambda/reminder_worker.py`, set environment variable `DATABASE_URL` pointing to RDS, and attach an EventBridge daily cron trigger (`cron(0 8 * * ? *)`).
