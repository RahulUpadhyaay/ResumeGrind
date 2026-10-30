from mangum import Mangum
from app.main import app

# WHY: Mangum is an adapter for running ASGI applications (like FastAPI) in AWS Lambda.
# This file serves as the entry point when deployed via AWS Lambda + API Gateway.

handler = Mangum(app)
