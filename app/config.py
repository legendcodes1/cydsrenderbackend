import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # Make sure this is set correctly
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("Database URL:", Config.SQLALCHEMY_DATABASE_URI)
