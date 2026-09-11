import azure.functions as func
from azure.communication.email import EmailClient

import json
import os
import re
import urllib.parse
import urllib.request


app = func.FunctionApp()


@app.route(
    route="contact",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def contact(req: func.HttpRequest) -> func.HttpResponse:

    try:
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
                    "error": "Security verification failed",
                    "turnstile": verification_result
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
            json.dumps({"error": "Invalid request"}),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as error:
        print(f"Contact function error: {type(error).__name__}: {error}")

        return func.HttpResponse(
            json.dumps({
                "error": "Server error",
                "type": type(error).__name__
            }),
            status_code=500,
            mimetype="application/json"
        )
