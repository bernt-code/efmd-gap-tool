import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    "https://bkhvztyvfkqzqqtoxxxi.supabase.co",
    os.getenv("SUPABASE_KEY")
)

print("=== PROGRAMMES ===")
result = supabase.table("programmes").select("*").limit(5).execute()
print(f"Found {len(result.data)} programmes")
for prog in result.data:
    print(f"  ID: {prog['id']}")
    print(f"  Name: {prog['programme_name']}")
    print(f"  Institution ID: {prog.get('institution_id', 'MISSING!')}")
    print()

print("=== INSTITUTIONS ===")
result = supabase.table("institutions").select("*").limit(5).execute()
print(f"Found {len(result.data)} institutions")
for inst in result.data:
    print(f"  {inst}")
    print()
