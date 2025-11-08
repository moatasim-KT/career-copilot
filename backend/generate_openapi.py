import json
from app.main import create_app

app = create_app()

openapi_schema = app.openapi()

with open("../frontend/openapi.json", "w") as f:
    json.dump(openapi_schema, f)
