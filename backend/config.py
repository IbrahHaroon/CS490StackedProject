import os

from dotenv import load_dotenv
from supabase import create_client

# Load .env automatically
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
