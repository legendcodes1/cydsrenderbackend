from dotenv import load_dotenv
import os

# Specify the full path to the .env file if necessary
dotenv_path = "C:/Users/legen/Documents/cydsnewbackend/.env"
result = load_dotenv(dotenv_path=dotenv_path)

print("Load result:", result)  # Should print True if the .env file was loaded successfully
print("DATABASE_URL:", os.getenv("DATABASE_URL"))  # Should print the value of DATABASE_URL
