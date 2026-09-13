import azure.functions as func
from azure.communication.email import EmailClient

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta


app = func.FunctionApp()


# --- Rate limiting (in-memory, per-instance) -------------------------------

_rate_limit_store = {}  # {ip: (window_start, count)}
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = timedelta(minutes=15)


def check_rate_limit(ip: str) -> bool:
    """Returns True if the request is allowed, False if rate-limited."""
    now = datetime.now(timezone.utc)
    window_start, count = _rate_limit_store.get(ip, (now, 0))

    if now - window_start > _RATE_LIMIT_WINDOW:
        _rate_limit_store[ip] = (now, 1)
        return True

    if count >= _RATE_LIMIT_MAX:
        return False

    _rate_limit_store[ip] = (window_start, count + 1)
    return True


# --- Sanitization ------------------------------------------------------

def sanitize_header(value: str) -> str:
    """Strip CR/LF and collapse whitespace to prevent header injection
    when a value is used in an email subject line or header field."""
    return re.sub(r"[\r\n]+", " ", value).strip()


@app.route(
    route="contact",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def contact(req: func.HttpRequest) -> func.HttpResponse:

    try:
        # Rate limit check (per client IP)
        client_ip = req.headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()

        if not check_rate_limit(client_ip):
            return func.HttpResponse(
                json.dumps({"error": "Too many requests. Please try again later."}),
                status_code=429,
                mimetype="application/json"
            )

        data = req.get_json()

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        company = str(data.get("company", "")).strip()
        message = str(data.get("message", "")).strip()
        website = str(data.get("website", "")).strip()
        turnstile_token = str(data.get("turnstileToken", "")).strip()

        # Honeypot check
        if website:
            return func.HttpResponse(
                json.dumps({"success": True}),
                status_code=200,
                mimetype="application/json"
            )

        # Required fields
        if not name or not email or not message:
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                status_code=400,
                mimetype="application/json"
            )

        # Length validation
        if len(name) > 100:
            return func.HttpResponse(
                json.dumps({"error": "Name is too long"}),
                status_code=400,
                mimetype="application/json"
            )

        if len(email) > 254:
            return func.HttpResponse(
                json.dumps({"error": "Email is too long"}),
                status_code=400,
                mimetype="application/json"
            )

        if len(company) > 150:
            return func.HttpResponse(
                json.dumps({"error": "Company name is too long"}),
                status_code=400,
                mimetype="application/json"
            )

        if len(message) > 3000:
            return func.HttpResponse(
                json.dumps({"error": "Message is too long"}),
                status_code=400,
                mimetype="application/json"
            )

        # Basic email validation
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(email_pattern, email):
            return func.HttpResponse(
                json.dumps({"error": "Invalid email address"}),
                status_code=400,
                mimetype="application/json"
            )

        # Sanitize values that get embedded in email headers/subject
        name = sanitize_header(name)
        company = sanitize_header(company)

        # Turnstile token must exist
        if not turnstile_token:
            return func.HttpResponse(
                json.dumps({"error": "Security verification missing"}),
                status_code=400,
                mimetype="application/json"
            )

        # Get Turnstile secret from Azure environment variables
        turnstile_secret = os.environ.get("TURNSTILE_SECRET_KEY")

        if not turnstile_secret:
            return func.HttpResponse(
                json.dumps({"error": "Server security configuration error"}),
                status_code=500,
                mimetype="application/json"
            )

        # Verify Turnstile token with Cloudflare
        verification_data = urllib.parse.urlencode({
            "secret": turnstile_secret,
            "response": turnstile_token
        }).encode("utf-8")

        verification_request = urllib.request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=verification_data,
            method="POST"
        )

        with urllib.request.urlopen(
            verification_request,
            timeout=10
        ) as verification_response:
            verification_result = json.loads(
                verification_response.read().decode("utf-8")
            )

        if not verification_result.get("success"):
            return func.HttpResponse(
                json.dumps({
                    "error": "Security verification failed"
                }),
                status_code=403,
                mimetype="application/json"
            )

        # Email configuration
        connection_string = os.environ.get("ACS_CONNECTION_STRING")
        sender_address = os.environ.get("ACS_SENDER_ADDRESS")
        recipient_email = os.environ.get("CONTACT_RECIPIENT_EMAIL")

        if not all([
            connection_string,
            sender_address,
            recipient_email
        ]):
            return func.HttpResponse(
                json.dumps({"error": "Email service configuration error"}),
                status_code=500,
                mimetype="application/json"
            )

        # Create Azure Communication Services Email client
        email_client = EmailClient.from_connection_string(
            connection_string
        )

        # Build email message
        email_message = {
            "senderAddress": sender_address,
            "recipients": {
                "to": [
                    {
                        "address": recipient_email
                    }
                ]
            },
            "content": {
                "subject": f"Portfolio contact from {name}",
                "plainText": (
                    "New portfolio contact submission\n\n"
                    f"Name: {name}\n"
                    f"Email: {email}\n"
                    f"Company: {company or 'Not provided'}\n\n"
                    f"Message:\n{message}"
                )
            },
            "replyTo": [
                {
                    "address": email
                }
            ]
        }

        # Send email
        poller = email_client.begin_send(email_message)
        email_result = poller.result()

        if email_result.get("status") != "Succeeded":
            return func.HttpResponse(
                json.dumps({"error": "Unable to send email"}),
                status_code=500,
                mimetype="application/json"
            )

        # Success response
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "message": "Message sent successfully"
            }),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError as error:
        print(f"Value error: {error}")

        return func.HttpResponse(
            json.dumps({
                "error": "Invalid request"
            }),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as error:
        print(f"Contact function error: {type(error).__name__}: {error}")

        return func.HttpResponse(
            json.dumps({
                "error": "Server error"
            }),
            status_code=500,
            mimetype="application/json"
        )
