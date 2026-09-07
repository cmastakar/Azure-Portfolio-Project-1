import azure.functions as func
import json
import re

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

        if website: 
            return func.HttpResponse(
                json.dumps({"success": True}),
                status_code=200,
                mimetype="application/json"
            )

        # Check required fields
        if not name or not email or not message:
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                status_code=400,
                mimetype="application/json"
            )

        # Length limits
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

        # Basic email format check
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(email_pattern, email):
            return func.HttpResponse(
                json.dumps({"error": "Invalid email address"}),
                status_code=400,
                mimetype="application/json"
            )

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
