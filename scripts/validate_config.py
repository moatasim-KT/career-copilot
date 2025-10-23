import os

def validate_config():
    required_vars = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "NEXT_PUBLIC_API_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            
    if missing_vars:
        print("Missing required environment variables:", missing_vars)
        exit(1)
        
    print("Configuration validated successfully.")

if __name__ == "__main__":
    validate_config()