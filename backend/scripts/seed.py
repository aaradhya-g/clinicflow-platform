"""
ClinicFlow Enterprise Database Seeder
Populates a fully working medical clinic environment:
- 3 Core Role Accounts (admin, doctor, receptionist)
- 4 Specialized Physicians with clinical profiles
- 15 Realistic Patients with MRNs, insurance statuses, and medical histories
- Active Clinic Queue & Appointments (Scheduled, Checked-In, In-Consultation, Completed)
- Recorded Triage Vitals
- Completed SOAP Consultations with Structured Prescriptions
- Immutable HIPAA Audit Logs
"""

import asyncio
from datetime import date, datetime, time, timedelta, timezone
import os
import sys
import uuid

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole, DoctorProfile
from app.models.patient import Patient, PatientMedicalHistory, InsuranceStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.clinical import VitalsRecord, ClinicalConsultation, Prescription
from app.models.audit import AuditLog


async def seed_database():
    print("Initializing database schema...", flush=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Checking for existing users...", flush=True)
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        existing_user = (await session.execute(select(User).limit(1))).scalar_one_or_none()
        if existing_user:
            print("Database already contains data. Skipping seed to prevent duplicate records.", flush=True)
            await engine.dispose()
            return

        print("Seeding ClinicFlow system accounts...", flush=True)
        # 1. System Accounts
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@clinicflow.med",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="Dr. Alexander Wright, MD (Chief Medical Officer)",
            role=UserRole.ADMIN,
            is_active=True,
        )
        receptionist_user = User(
            id=uuid.uuid4(),
            email="receptionist@clinicflow.med",
            password_hash=get_password_hash("ReceptionPass123!"),
            full_name="Maria Hernandez (Head Receptionist)",
            role=UserRole.RECEPTIONIST,
            is_active=True,
        )
        session.add_all([admin_user, receptionist_user])

        # 2. Four Specialized Doctors
        doctors_meta = [
            {
                "email": "doctor.chen@clinicflow.med",
                "password": "DoctorPass123!",
                "name": "Dr. Sarah Chen, MD",
                "specialty": "Cardiology",
                "license": "MED-CA-88491",
                "room": "Room 302B",
                "fee": 220.00,
            },
            {
                "email": "doctor.vance@clinicflow.med",
                "password": "DoctorPass123!",
                "name": "Dr. Marcus Vance, MD",
                "specialty": "Internal Medicine",
                "license": "MED-CA-92104",
                "room": "Room 205A",
                "fee": 180.00,
            },
            {
                "email": "doctor.rostova@clinicflow.med",
                "password": "DoctorPass123!",
                "name": "Dr. Elena Rostova, MD",
                "specialty": "Pediatrics",
                "license": "MED-CA-77312",
                "room": "Room 108C",
                "fee": 160.00,
            },
            {
                "email": "doctor.wilson@clinicflow.med",
                "password": "DoctorPass123!",
                "name": "Dr. James Wilson, MD",
                "specialty": "Orthopedics",
                "license": "MED-CA-64903",
                "room": "Room 410A",
                "fee": 250.00,
            },
        ]

        doctor_profiles: list[DoctorProfile] = []
        for d in doctors_meta:
            doc_user = User(
                id=uuid.uuid4(),
                email=d["email"],
                password_hash=get_password_hash(d["password"]),
                full_name=d["name"],
                role=UserRole.DOCTOR,
                is_active=True,
            )
            session.add(doc_user)
            await session.flush()

            profile = DoctorProfile(
                id=uuid.uuid4(),
                user_id=doc_user.id,
                specialty=d["specialty"],
                license_number=d["license"],
                room_number=d["room"],
                consultation_fee=d["fee"],
                is_available=True,
            )
            session.add(profile)
            doctor_profiles.append(profile)

        await session.flush()
        print(f"Created system users and {len(doctor_profiles)} doctors.")

        # 3. 15 Realistic Patients
        patients_data = [
            {
                "first": "Eleanor", "last": "Vance", "dob": date(1982, 5, 14), "gender": "Female",
                "phone": "(555) 234-8901", "email": "eleanor.vance@example.com",
                "address": "742 Evergreen Terrace, Springfield", "emergency": "Robert Vance (Spouse) - (555) 234-8902",
                "ins_provider": "Blue Cross Blue Shield", "ins_policy": "BCBS-9948210", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "A+", "allergies": ["Penicillin"], "chronic": ["Hypertension"], "meds": ["Lisinopril 10mg QD"],
            },
            {
                "first": "Marcus", "last": "Aurelius", "dob": date(1975, 11, 22), "gender": "Male",
                "phone": "(555) 345-6789", "email": "marcus.aurelius@example.com",
                "address": "1200 Palatine Hill Way, Suite 4", "emergency": "Faustina Aurelius (Wife) - (555) 345-6790",
                "ins_provider": "Aetna Health", "ins_policy": "AET-7738291", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "O+", "allergies": ["Sulfa drugs", "Latex"], "chronic": ["Type 2 Diabetes", "Hyperlipidemia"], "meds": ["Metformin 500mg BID", "Atorvastatin 20mg QHS"],
            },
            {
                "first": "Sophia", "last": "Patel", "dob": date(1994, 3, 9), "gender": "Female",
                "phone": "(555) 456-7890", "email": "sophia.patel@example.com",
                "address": "45 Market Street, Apt 12B", "emergency": "Arjun Patel (Brother) - (555) 456-7891",
                "ins_provider": "UnitedHealthcare", "ins_policy": "UHC-1029384", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "B+", "allergies": ["Peanuts"], "chronic": ["Asthma"], "meds": ["Albuterol HFA Inhaler PRN"],
            },
            {
                "first": "David", "last": "Kim", "dob": date(1968, 8, 30), "gender": "Male",
                "phone": "(555) 567-8901", "email": "david.kim@example.com",
                "address": "88 Ocean Drive, Pacifica", "emergency": "Sun-hee Kim (Daughter) - (555) 567-8902",
                "ins_provider": "Cigna Healthcare", "ins_policy": "CIG-4491029", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "O-", "allergies": ["Aspirin"], "chronic": ["Osteoarthritis", "GERD"], "meds": ["Omeprazole 20mg QD"],
            },
            {
                "first": "Amara", "last": "Okafor", "dob": date(1991, 1, 17), "gender": "Female",
                "phone": "(555) 678-9012", "email": "amara.okafor@example.com",
                "address": "310 Magnolia Lane", "emergency": "Chidi Okafor (Spouse) - (555) 678-9013",
                "ins_provider": "Kaiser Permanente", "ins_policy": "KP-9912034", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "AB+", "allergies": [], "chronic": ["Migraines"], "meds": ["Sumatriptan 50mg PRN"],
            },
            {
                "first": "Liam", "last": "O'Connor", "dob": date(2001, 7, 4), "gender": "Male",
                "phone": "(555) 789-0123", "email": "liam.oconnor@example.com",
                "address": "15 University Ave, Apt 3", "emergency": "Mary O'Connor (Mother) - (555) 789-0124",
                "ins_provider": "Anthem Blue Cross", "ins_policy": "ANT-3391024", "ins_status": InsuranceStatus.PENDING,
                "blood": "A-", "allergies": ["Shellfish"], "chronic": [], "meds": [],
            },
            {
                "first": "Isabella", "last": "Santos", "dob": date(1987, 12, 19), "gender": "Female",
                "phone": "(555) 890-1234", "email": "isabella.santos@example.com",
                "address": "62 Harbor Boulevard", "emergency": "Mateo Santos (Brother) - (555) 890-1235",
                "ins_provider": None, "ins_policy": None, "ins_status": InsuranceStatus.UNINSURED,
                "blood": "O+", "allergies": ["Codeine"], "chronic": ["Hypothyroidism"], "meds": ["Levothyroxine 75mcg QD"],
            },
            {
                "first": "Lucas", "last": "Muller", "dob": date(1980, 4, 25), "gender": "Male",
                "phone": "(555) 901-2345", "email": "lucas.muller@example.com",
                "address": "504 Redwood Highway", "emergency": "Hannah Muller (Spouse) - (555) 901-2346",
                "ins_provider": "Humana", "ins_policy": "HUM-8812904", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "B-", "allergies": [], "chronic": ["Chronic Low Back Pain"], "meds": ["Ibuprofen 400mg PRN"],
            },
            {
                "first": "Chloe", "last": "Dubois", "dob": date(1996, 9, 12), "gender": "Female",
                "phone": "(555) 012-3456", "email": "chloe.dubois@example.com",
                "address": "212 Pine Crest Road", "emergency": "Jean Dubois (Father) - (555) 012-3457",
                "ins_provider": "UnitedHealthcare", "ins_policy": "UHC-9923841", "ins_status": InsuranceStatus.PENDING,
                "blood": "A+", "allergies": ["Amoxicillin"], "chronic": ["Allergic Rhinitis"], "meds": ["Cetirizine 10mg QD"],
            },
            {
                "first": "Benjamin", "last": "Taylor", "dob": date(1959, 2, 18), "gender": "Male",
                "phone": "(555) 123-4567", "email": "benjamin.taylor@example.com",
                "address": "90 Cedar Ridge Court", "emergency": "Evelyn Taylor (Wife) - (555) 123-4568",
                "ins_provider": "Medicare Part B", "ins_policy": "MED-6612984", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "O+", "allergies": [], "chronic": ["Coronary Artery Disease", "Hypertension"], "meds": ["Aspirin 81mg QD", "Metoprolol 25mg BID"],
            },
            {
                "first": "Amina", "last": "Al-Mansoor", "dob": date(1989, 6, 28), "gender": "Female",
                "phone": "(555) 234-5678", "email": "amina.mansoor@example.com",
                "address": "140 Sunset Boulevard", "emergency": "Tariq Mansoor (Spouse) - (555) 234-5679",
                "ins_provider": "Blue Cross Blue Shield", "ins_policy": "BCBS-4421092", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "AB-", "allergies": ["Iodine Contrast"], "chronic": ["Polycystic Ovary Syndrome"], "meds": ["Metformin 500mg QD"],
            },
            {
                "first": "Ethan", "last": "Wright", "dob": date(2015, 10, 8), "gender": "Male",
                "phone": "(555) 345-6780", "email": "sarah.wright.parent@example.com",
                "address": "33 Maple Court", "emergency": "Sarah Wright (Mother) - (555) 345-6780",
                "ins_provider": "Aetna Health", "ins_policy": "AET-5510293", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "O+", "allergies": ["Peanuts", "Eggs"], "chronic": ["Eczema"], "meds": ["Hydrocortisone Cream 1% PRN"],
            },
            {
                "first": "Grace", "last": "Holloway", "dob": date(1972, 7, 15), "gender": "Female",
                "phone": "(555) 456-7892", "email": "grace.holloway@example.com",
                "address": "77 Beacon Street", "emergency": "Arthur Holloway (Brother) - (555) 456-7893",
                "ins_provider": None, "ins_policy": None, "ins_status": InsuranceStatus.UNINSURED,
                "blood": "B+", "allergies": [], "chronic": ["Generalized Anxiety Disorder"], "meds": ["Sertraline 50mg QD"],
            },
            {
                "first": "Oliver", "last": "Thorne", "dob": date(1984, 11, 3), "gender": "Male",
                "phone": "(555) 567-8903", "email": "oliver.thorne@example.com",
                "address": "180 Birch Hill Road", "emergency": "Clara Thorne (Spouse) - (555) 567-8904",
                "ins_provider": "Cigna Healthcare", "ins_policy": "CIG-8829104", "ins_status": InsuranceStatus.PENDING,
                "blood": "A+", "allergies": ["Penicillin"], "chronic": ["Acid Reflux"], "meds": ["Famotidine 20mg BID"],
            },
            {
                "first": "Mia", "last": "Kowalski", "dob": date(1998, 4, 11), "gender": "Female",
                "phone": "(555) 678-9014", "email": "mia.kowalski@example.com",
                "address": "95 Riverview Drive", "emergency": "Piotr Kowalski (Father) - (555) 678-9015",
                "ins_provider": "Anthem Blue Cross", "ins_policy": "ANT-9901824", "ins_status": InsuranceStatus.VERIFIED,
                "blood": "O-", "allergies": [], "chronic": ["Iron Deficiency Anemia"], "meds": ["Ferrous Sulfate 325mg QD"],
            },
        ]

        patients: list[Patient] = []
        for idx, p in enumerate(patients_data):
            patient_id = uuid.uuid4()
            mrn = f"CF-2026-{(idx + 1):04d}"
            pat = Patient(
                id=patient_id,
                mrn=mrn,
                first_name=p["first"],
                last_name=p["last"],
                date_of_birth=p["dob"],
                gender=p["gender"],
                phone=p["phone"],
                email=p["email"],
                address=p["address"],
                emergency_contact=p["emergency"],
                insurance_provider=p["ins_provider"],
                insurance_policy_number=p["ins_policy"],
                insurance_status=p["ins_status"],
            )
            session.add(pat)

            history = PatientMedicalHistory(
                id=uuid.uuid4(),
                patient_id=patient_id,
                blood_type=p["blood"],
                allergies=p["allergies"],
                chronic_conditions=p["chronic"],
                current_medications=p["meds"],
                surgical_history="Appendectomy (2012)" if idx % 3 == 0 else "None",
            )
            session.add(history)
            patients.append(pat)

        await session.flush()
        print(f"Created {len(patients)} patients with complete medical histories.")

        # 4. Realistic Appointments & Queue States
        today = date.today()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)

        # Primary Doctor: Dr. Sarah Chen (Cardiology)
        dr_chen = doctor_profiles[0]
        dr_vance = doctor_profiles[1]
        dr_rostova = doctor_profiles[2]
        dr_wilson = doctor_profiles[3]

        appointments_to_create = [
            # TODAY's Queue for Dr. Chen:
            # 1. In-Consultation right now (Eleanor Vance)
            {
                "patient": patients[0], "doctor": dr_chen, "date": today,
                "start": time(9, 30), "end": time(10, 0), "status": AppointmentStatus.IN_CONSULTATION,
                "reason": "Follow-up for episodic heart palpitations and resting hypertension.",
                "vitals": {"sys": 142, "dia": 92, "hr": 84, "temp": 36.8, "spo2": 98, "rr": 16, "wt": 68.5, "ht": 165.0},
            },
            # 2. Checked-In, Triage Vitals Complete, Waiting for Doctor (Marcus Aurelius)
            {
                "patient": patients[1], "doctor": dr_chen, "date": today,
                "start": time(10, 0), "end": time(10, 30), "status": AppointmentStatus.CHECKED_IN,
                "reason": "Evaluation of fasting blood sugars and borderline chest tightness.",
                "vitals": {"sys": 138, "dia": 86, "hr": 76, "temp": 36.6, "spo2": 99, "rr": 14, "wt": 82.0, "ht": 178.0},
            },
            # 3. Checked-In, Waiting for Vitals Intake (Sophia Patel)
            {
                "patient": patients[2], "doctor": dr_chen, "date": today,
                "start": time(10, 30), "end": time(11, 0), "status": AppointmentStatus.CHECKED_IN,
                "reason": "Shortness of breath on exertion following cold weather exposure.",
                "vitals": None,
            },
            # 4. Scheduled (David Kim)
            {
                "patient": patients[3], "doctor": dr_chen, "date": today,
                "start": time(11, 0), "end": time(11, 30), "status": AppointmentStatus.SCHEDULED,
                "reason": "Routine 6-month cardiovascular checkup and ECG review.",
                "vitals": None,
            },
            # TODAY's Queue for Dr. Vance (Internal Medicine):
            # 5. Checked-In with Vitals (Amara Okafor)
            {
                "patient": patients[4], "doctor": dr_vance, "date": today,
                "start": time(9, 30), "end": time(10, 0), "status": AppointmentStatus.CHECKED_IN,
                "reason": "Recurrent migraine headaches with visual aura.",
                "vitals": {"sys": 118, "dia": 74, "hr": 70, "temp": 37.0, "spo2": 99, "rr": 16, "wt": 62.0, "ht": 168.0},
            },
            # 6. Scheduled (Liam O'Connor)
            {
                "patient": patients[5], "doctor": dr_vance, "date": today,
                "start": time(10, 30), "end": time(11, 0), "status": AppointmentStatus.SCHEDULED,
                "reason": "Annual comprehensive wellness physical exam.",
                "vitals": None,
            },
            # TODAY's Queue for Dr. Wilson (Orthopedics):
            # 7. Scheduled (Lucas Muller)
            {
                "patient": patients[7], "doctor": dr_wilson, "date": today,
                "start": time(11, 30), "end": time(12, 0), "status": AppointmentStatus.SCHEDULED,
                "reason": "Chronic lumbar spine pain radiating to right gluteal region.",
                "vitals": None,
            },
            # TOMORROW's Appointments (Eligible for 24h SES Reminders):
            # 8. Dr. Chen
            {
                "patient": patients[8], "doctor": dr_chen, "date": tomorrow,
                "start": time(9, 30), "end": time(10, 0), "status": AppointmentStatus.SCHEDULED,
                "reason": "Pre-operative cardiology risk clearance.",
                "vitals": None,
            },
            # 9. Dr. Wilson
            {
                "patient": patients[9], "doctor": dr_wilson, "date": tomorrow,
                "start": time(10, 0), "end": time(10, 30), "status": AppointmentStatus.SCHEDULED,
                "reason": "Right knee osteoarthritis follow-up after corticosteroid injection.",
                "vitals": None,
            },
            # HISTORICAL Completed Consultations (Yesterday & past):
            # 10. Benjamin Taylor with Dr. Chen (Completed + Notes + Prescriptions)
            {
                "patient": patients[9], "doctor": dr_chen, "date": yesterday,
                "start": time(9, 0), "end": time(9, 30), "status": AppointmentStatus.COMPLETED,
                "reason": "Coronary artery disease management and medication tolerance check.",
                "vitals": {"sys": 134, "dia": 82, "hr": 68, "temp": 36.7, "spo2": 98, "rr": 14, "wt": 79.0, "ht": 175.0},
                "consultation": {
                    "complaint": "Patient presents for 3-month review of stable ischemic heart disease.",
                    "notes": (
                        "SUBJECTIVE: 67yo male reports compliance with daily low-dose aspirin and beta-blocker therapy. "
                        "Denies orthopnea, paroxysmal nocturnal dyspnea, or lower extremity edema.\n\n"
                        "OBJECTIVE: BP 134/82 mmHg, HR 68 bpm regular. S1/S2 present, no murmurs, rubs, or gallops. "
                        "Lungs clear to auscultation bilaterally.\n\n"
                        "ASSESSMENT: Chronic ischemic heart disease with well-controlled hypertension.\n\n"
                        "PLAN: Continue Metoprolol Succinate 25mg QD. Add Rosuvastatin 10mg QHS for LDL target < 70mg/dL. "
                        "Re-check lipid panel in 12 weeks."
                    ),
                    "diagnoses": [
                        {"code": "I25.10", "name": "Atherosclerotic heart disease of native coronary artery"},
                        {"code": "I10", "name": "Essential (primary) hypertension"},
                    ],
                    "prescriptions": [
                        {"med": "Rosuvastatin Calcium", "dose": "10mg", "freq": "Once daily at bedtime", "dur": "90 days", "inst": "Take with water. Monitor for unexplained muscle soreness."},
                        {"med": "Metoprolol Succinate ER", "dose": "25mg", "freq": "Once daily in morning", "dur": "90 days", "inst": "Do not abruptly discontinue."},
                    ],
                },
            },
            # 11. David Kim with Dr. Wilson (Completed)
            {
                "patient": patients[3], "doctor": dr_wilson, "date": yesterday,
                "start": time(14, 0), "end": time(14, 30), "status": AppointmentStatus.COMPLETED,
                "reason": "Bilateral knee stiffness, aggravated by stairs.",
                "vitals": {"sys": 128, "dia": 80, "hr": 72, "temp": 36.5, "spo2": 99, "rr": 16, "wt": 74.0, "ht": 172.0},
                "consultation": {
                    "complaint": "Persistent bilateral knee discomfort for 6 months.",
                    "notes": (
                        "SUBJECTIVE: 58yo male with gradual onset crepitus and stiffness.\n"
                        "OBJECTIVE: Mild joint effusion right knee, range of motion 0-120 degrees with medial joint line tenderness.\n"
                        "ASSESSMENT: Bilateral primary osteoarthritis of knee (M17.0).\n"
                        "PLAN: Physical therapy prescription 2x weekly for 6 weeks. Topical NSAID gel as needed."
                    ),
                    "diagnoses": [
                        {"code": "M17.0", "name": "Bilateral primary osteoarthritis of knee"},
                    ],
                    "prescriptions": [
                        {"med": "Diclofenac Sodium 1% Gel", "dose": "4 grams", "freq": "Apply to affected knee 4 times daily", "dur": "30 days", "inst": "Wash hands thoroughly after application."},
                    ],
                },
            },
        ]

        for item in appointments_to_create:
            apt_id = uuid.uuid4()
            apt = Appointment(
                id=apt_id,
                patient_id=item["patient"].id,
                doctor_id=item["doctor"].id,
                appointment_date=item["date"],
                start_time=item["start"],
                end_time=item["end"],
                status=item["status"],
                reason_for_visit=item["reason"],
                reminder_sent=False,
            )
            session.add(apt)
            await session.flush()

            # Record vitals if configured
            if item.get("vitals"):
                v = item["vitals"]
                ht_m = v["ht"] / 100.0
                bmi = round(v["wt"] / (ht_m * ht_m), 1)
                vitals = VitalsRecord(
                    id=uuid.uuid4(),
                    appointment_id=apt_id,
                    patient_id=item["patient"].id,
                    recorded_by_user_id=receptionist_user.id,
                    systolic_bp=v["sys"],
                    diastolic_bp=v["dia"],
                    heart_rate=v["hr"],
                    temperature_c=v["temp"],
                    spo2_percentage=v["spo2"],
                    respiratory_rate=v["rr"],
                    weight_kg=v["wt"],
                    height_cm=v["ht"],
                    bmi=bmi,
                    recorded_at=datetime.now(timezone.utc),
                )
                session.add(vitals)

            # Record consultation if configured
            if item.get("consultation"):
                c = item["consultation"]
                consult = ClinicalConsultation(
                    id=uuid.uuid4(),
                    appointment_id=apt_id,
                    patient_id=item["patient"].id,
                    doctor_id=item["doctor"].id,
                    chief_complaint=c["complaint"],
                    clinical_notes=c["notes"],
                    diagnosis_codes=c["diagnoses"],
                    follow_up_date=today + timedelta(days=90),
                )
                session.add(consult)
                await session.flush()

                for rx in c.get("prescriptions", []):
                    prescription = Prescription(
                        id=uuid.uuid4(),
                        consultation_id=consult.id,
                        patient_id=item["patient"].id,
                        medication_name=rx["med"],
                        dosage=rx["dose"],
                        frequency=rx["freq"],
                        duration=rx["dur"],
                        instructions=rx["inst"],
                    )
                    session.add(prescription)

        # 5. Seed HIPAA Audit Logs
        print("Seeding HIPAA compliance audit log records...")
        audit_events = [
            ("LOGIN_SUCCESS", "USER", str(admin_user.id), admin_user.id, "admin", {"email": admin_user.email}),
            ("LOGIN_SUCCESS", "USER", str(receptionist_user.id), receptionist_user.id, "receptionist", {"email": receptionist_user.email}),
            ("REGISTER_PATIENT", "PATIENT", str(patients[0].id), receptionist_user.id, "receptionist", {"mrn": patients[0].mrn, "patient": "Eleanor Vance"}),
            ("REGISTER_PATIENT", "PATIENT", str(patients[1].id), receptionist_user.id, "receptionist", {"mrn": patients[1].mrn, "patient": "Marcus Aurelius"}),
            ("VERIFY_INSURANCE", "PATIENT", str(patients[0].id), receptionist_user.id, "receptionist", {"carrier": "BCBS", "status": "Verified"}),
            ("CREATE_APPOINTMENT", "APPOINTMENT", "apt-chen-01", receptionist_user.id, "receptionist", {"doctor": "Dr. Sarah Chen", "slot": "09:30 AM"}),
            ("RECORD_VITALS", "VITALS", "vitals-01", receptionist_user.id, "receptionist", {"bp": "142/92", "pulse": 84, "spo2": 98}),
            ("READ_PATIENT_EHR", "PATIENT", str(patients[0].id), doctor_profiles[0].user_id, "doctor", {"reason": "Cardiology intake"}),
            ("COMPLETE_CONSULTATION", "CONSULTATION", "consult-01", doctor_profiles[0].user_id, "doctor", {"diagnoses_count": 2, "prescriptions_count": 2}),
        ]

        for act, res_type, res_id, u_id, r, details in audit_events:
            audit_log = AuditLog(
                id=uuid.uuid4(),
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=15),
                user_id=u_id,
                role=r,
                action=act,
                resource_type=res_type,
                resource_id=res_id,
                ip_address="192.168.1.100",
                details=details,
            )
            session.add(audit_log)

        await session.commit()
        print("\n=======================================================")
        print("   ClinicFlow Seed Complete! Demo Accounts Ready:    ")
        print("=======================================================")
        print(" [ADMIN]        admin@clinicflow.med        | AdminPass123!")
        print(" [DOCTOR]       doctor.chen@clinicflow.med  | DoctorPass123!")
        print(" [RECEPTIONIST] receptionist@clinicflow.med | ReceptionPass123!")
        print("=======================================================\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
