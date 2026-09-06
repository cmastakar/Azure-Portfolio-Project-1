import azure.functions as func
import json

app = func.FunctionApp()

@app.route(route="contact", methods=["POST"])
def contact(req: func.HttpRequest) -> func.HttpResponse:

    try:
        data = req.get_json()

        name = data.get("name")
        email = data.get("email")
        company = data.get("company")
        message = data.get("message")

        if not name or not email or not message:
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
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

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid request"}),
            status_code=400,
            mimetype="application/json"
        )
