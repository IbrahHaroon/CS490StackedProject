import os

from dotenv import load_dotenv

try:
    from supabase import create_client
except ImportError:
    create_client = None

# Load .env automatically
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if create_client and SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None
