import os
import sys
import requests
from sqlalchemy import create_engine

# Check environment variables
required_env_vars = ["OPENAI_API_KEY", "DATABASE_URL", "SECRET_KEY"]
missing_vars = [var for var in required_env_vars if var not in os.environ]
if missing_vars:
    print(f"Missing environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Check database connection
db_url = os.environ["DATABASE_URL"]
try:
    engine = create_engine(db_url)
    with engine.connect() as connection:
        connection.execute("SELECT 1")
    print("Database connection: OK")
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)

# Check application health
app_url = "http://localhost:8000/health"
try:
    response = requests.get(app_url)
    if response.status_code == 200:
        print("Application health: OK")
    else:
        print(f"Application health check failed with status code: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"Application health check failed: {e}")
    sys.exit(1)

print("All checks passed!")