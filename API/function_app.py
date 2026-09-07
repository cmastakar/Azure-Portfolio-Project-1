import azure.functions as func
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

        # Get secret from Azure environment variable
        turnstile_secret = os.environ.get("TURNSTILE_SECRET_KEY")

        if not turnstile_secret:
            return func.HttpResponse(
                json.dumps({"error": "Server security configuration error"}),
                status_code=500,
                mimetype="application/json"
            )

        # Verify token with Cloudflare
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
                json.dumps({"error": "Security verification failed"}),
                status_code=403,
                mimetype="application/json"
            )

        # Success
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "message": "Contact request received"
            }),
            status_code=200,
            mimetype="application/json"
        )

    except (ValueError, TypeError):
        return func.HttpResponse(
            json.dumps({"error": "Invalid request"}),
            status_code=400,
            mimetype="application/json"
        )

    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "Server error"}),
            status_code=500,
            mimetype="application/json"
        )
