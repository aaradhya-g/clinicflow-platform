"""
ClinicFlow 24-Hour Appointment Reminder Worker
AWS Lambda Handler triggered by Amazon EventBridge Cron.
Queries upcoming appointments in the next 24 hours, dispatches reminder emails via Amazon SES,
and marks reminders as sent in PostgreSQL.
"""

import os
import sys
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

# Setup structured logging
logger = logging.getLogger("clinicflow.reminder_worker")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)

# Configuration via environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/clinicflow"
)
SES_REGION = os.getenv("AWS_REGION", "us-east-1")
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL", "reminders@clinicflow.med")
MOCK_SES = os.getenv("MOCK_SES", "false").lower() in ("true", "1", "yes")

# Try importing boto3
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed. Running in forced mock mode.")


def get_ses_client():
    """Initializes and returns Amazon SES client if credentials exist and mock mode is off."""
    if MOCK_SES or not BOTO3_AVAILABLE:
        return None
    try:
        return boto3.client("ses", region_name=SES_REGION)
    except Exception as e:
        logger.warning(f"Could not initialize boto3 SES client ({e}). Falling back to mock mode.")
        return None


def generate_email_content(
    patient_name: str,
    doctor_name: str,
    specialty: str,
    appointment_date: str,
    start_time: str,
    room_number: str,
    clinic_name: str = "ClinicFlow Health Center"
) -> Dict[str, str]:
    """Generates accessible, professional clinical email content."""
    subject = f"Appointment Reminder: Your Visit Tomorrow at {clinic_name}"
    
    text_body = f"""Hello {patient_name},

This is a reminder of your upcoming medical consultation at {clinic_name}.

Appointment Details:
- Doctor: Dr. {doctor_name} ({specialty})
- Date: {appointment_date}
- Time: {start_time}
- Room / Suite: {room_number}

Please arrive 15 minutes early for triage vitals intake and bring your photo ID and insurance card.
If you need to reschedule or cancel, please contact the clinic reception immediately.

Best regards,
{clinic_name} Care Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FFFFFF; color: #1E1B1E; margin: 0; padding: 24px; }}
    .container {{ max-width: 580px; margin: 0 auto; border: 1px solid #FCE8E8; border-radius: 8px; background-color: #FFF8F8; padding: 32px; }}
    .header {{ border-bottom: 2px solid #E11D48; padding-bottom: 16px; margin-bottom: 24px; }}
    .title {{ color: #E11D48; font-size: 22px; font-weight: 700; margin: 0; }}
    .badge {{ display: inline-block; background-color: #FFF0F0; color: #BE123C; border: 1px solid #FCE8E8; padding: 4px 10px; border-radius: 9999px; font-size: 13px; font-weight: 600; margin-top: 8px; }}
    .card {{ background: #FFFFFF; border: 1px solid #FCE8E8; border-radius: 6px; padding: 20px; margin: 20px 0; }}
    .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #FFF0F0; }}
    .detail-label {{ color: #645D62; font-weight: 500; }}
    .detail-value {{ font-weight: 600; color: #1E1B1E; }}
    .footer {{ font-size: 13px; color: #645D62; margin-top: 24px; text-align: center; border-top: 1px solid #FCE8E8; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 class="title">{clinic_name}</h1>
      <span class="badge">Appointment Reminder</span>
    </div>
    <p>Dear <strong>{patient_name}</strong>,</p>
    <p>You have an upcoming consultation scheduled with our clinical team tomorrow:</p>
    <div class="card">
      <div class="detail-row">
        <span class="detail-label">Physician:</span>
        <span class="detail-value">Dr. {doctor_name} ({specialty})</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Date:</span>
        <span class="detail-value">{appointment_date}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Scheduled Time:</span>
        <span class="detail-value">{start_time}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Clinic Location:</span>
        <span class="detail-value">Room {room_number}</span>
      </div>
    </div>
    <p style="font-size: 14px; color: #645D62;">
      Please arrive 15 minutes prior to your scheduled time for intake of vital signs.
      Bring your health insurance card and current medication list.
    </p>
    <div class="footer">
      ClinicFlow Platform &bull; HIPAA Compliant Healthcare Delivery &bull; (800) 555-FLOW
    </div>
  </div>
</body>
</html>"""

    return {"subject": subject, "text": text_body, "html": html_body}


def dispatch_reminder_email(
    ses_client,
    recipient_email: str,
    content: Dict[str, str]
) -> bool:
    """Dispatches email via AWS SES or outputs formatted mock payload."""
    if ses_client is None:
        # Mock mode execution
        logger.info(
            f"[MOCK SES DISPATCH] -> Recipient: {recipient_email} | Subject: '{content['subject']}'"
        )
        return True

    try:
        response = ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": content["subject"], "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": content["text"], "Charset": "UTF-8"},
                    "Html": {"Data": content["html"], "Charset": "UTF-8"},
                },
            },
        )
        logger.info(f"SES email dispatched successfully! MessageId: {response.get('MessageId')}")
        return True
    except (ClientError, NoCredentialsError) as e:
        logger.error(f"Failed to dispatch SES email to {recipient_email}: {e}")
        return False


def query_and_process_reminders(
    conn_str: str,
    ses_client,
    target_date: Optional[date] = None,
    mock_records: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Finds upcoming 24h appointments where reminder_sent is False and status is 'Scheduled',
    sends reminders, and marks them updated.
    Supports mock_records for standalone/offline integration testing.
    """
    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    results = {
        "target_date": str(target_date),
        "total_eligible": 0,
        "sent_successfully": 0,
        "failed": 0,
        "processed_ids": [],
    }

    # If mock records are directly passed (used in pytest/offline runner)
    if mock_records is not None:
        for record in mock_records:
            if record.get("appointment_date") == str(target_date) and not record.get("reminder_sent"):
                results["total_eligible"] += 1
                email_content = generate_email_content(
                    patient_name=record["patient_name"],
                    doctor_name=record["doctor_name"],
                    specialty=record.get("specialty", "General Medicine"),
                    appointment_date=record["appointment_date"],
                    start_time=record["start_time"],
                    room_number=record.get("room_number", "101"),
                )
                success = dispatch_reminder_email(ses_client, record["patient_email"], email_content)
                if success:
                    results["sent_successfully"] += 1
                    results["processed_ids"].append(record["id"])
                    record["reminder_sent"] = True
                else:
                    results["failed"] += 1
        return results

    # Live Database Execution (PostgreSQL)
    try:
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        query = """
            SELECT
                a.id,
                a.appointment_date,
                a.start_time,
                p.first_name || ' ' || p.last_name AS patient_name,
                p.email AS patient_email,
                u.full_name AS doctor_name,
                dp.specialty,
                dp.room_number
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctor_profiles dp ON a.doctor_id = dp.id
            JOIN users u ON dp.user_id = u.id
            WHERE a.appointment_date = %s
              AND a.status = 'Scheduled'
              AND a.reminder_sent = FALSE;
        """
        cursor.execute(query, (target_date,))
        rows = cursor.fetchall()
        results["total_eligible"] = len(rows)

        for row in rows:
            appointment_id = str(row["id"])
            email_content = generate_email_content(
                patient_name=row["patient_name"],
                doctor_name=row["doctor_name"],
                specialty=row["specialty"] or "General Medicine",
                appointment_date=str(row["appointment_date"]),
                start_time=str(row["start_time"]),
                room_number=row["room_number"] or "Consultation Suite",
            )
            success = dispatch_reminder_email(ses_client, row["patient_email"], email_content)
            if success:
                update_query = "UPDATE appointments SET reminder_sent = TRUE WHERE id = %s;"
                cursor.execute(update_query, (appointment_id,))
                conn.commit()
                results["sent_successfully"] += 1
                results["processed_ids"].append(appointment_id)
            else:
                results["failed"] += 1

        cursor.close()
        conn.close()

    except Exception as exc:
        logger.error(f"Database error during reminder dispatch: {exc}")
        results["error"] = str(exc)

    return results


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entrypoint triggered by Amazon EventBridge Cron."""
    logger.info("ClinicFlow Appointment Reminder Lambda invoked.")
    logger.info(f"Incoming Event: {json.dumps(event)}")

    ses_client = get_ses_client()
    results = query_and_process_reminders(
        conn_str=DATABASE_URL,
        ses_client=ses_client
    )

    logger.info(f"Reminder dispatch finished: {results}")
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }


if __name__ == "__main__":
    # Local CLI invocation
    print("=== ClinicFlow 24-Hour Reminder Worker Local Runner ===")
    mock_data = [
        {
            "id": "apt-test-001",
            "patient_name": "Eleanor Vance",
            "patient_email": "eleanor.vance@example.com",
            "doctor_name": "Sarah Chen",
            "specialty": "Cardiology",
            "appointment_date": str(date.today() + timedelta(days=1)),
            "start_time": "09:30 AM",
            "room_number": "302B",
            "reminder_sent": False,
        },
        {
            "id": "apt-test-002",
            "patient_name": "Marcus Aurelius",
            "patient_email": "marcus.a@example.com",
            "doctor_name": "James Wilson",
            "specialty": "Orthopedics",
            "appointment_date": str(date.today() + timedelta(days=1)),
            "start_time": "11:00 AM",
            "room_number": "104A",
            "reminder_sent": False,
        }
    ]
    res = query_and_process_reminders(
        conn_str=DATABASE_URL,
        ses_client=None, # Force mock
        mock_records=mock_data
    )
    print("Result Summary:", json.dumps(res, indent=2))
