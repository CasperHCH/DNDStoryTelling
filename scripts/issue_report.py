import os
import sys
import requests
from sqlalchemy import create_engine

def check_env_vars():
    print("Checking environment variables...")
    required_env_vars = ["OPENAI_API_KEY", "DATABASE_URL", "SECRET_KEY"]
    missing_vars = [var for var in required_env_vars if var not in os.environ]
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    print("All required environment variables are set.")
    return True

def check_database():
    print("Checking database connection...")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is not set.")
        return False
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print("Database connection: OK")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def check_application_health():
    print("Checking application health...")
    app_url = "http://localhost:8000/health"
    try:
        response = requests.get(app_url)
        if response.status_code == 200:
            print("Application health: OK")
            return True
        else:
            print(f"Application health check failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Application health check failed: {e}")
        return False

def main():
    print("Starting issue report...")
    env_ok = check_env_vars()
    db_ok = check_database()
    app_ok = check_application_health()

    if env_ok and db_ok and app_ok:
        print("\nAll checks passed! No issues detected.")
    else:
        print("\nIssues detected. Please review the above messages.")
        sys.exit(1)

if __name__ == "__main__":
    main()