import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    "https://bkhvztyvfkqzqqtoxxxi.supabase.co",
    os.getenv("SUPABASE_KEY")
)

# Delete the 3 empty institutions
empty_ids = [
    '06ad117d-5b1a-48fd-ac71-36aedb61083b',
    '4edc158d-cb70-488d-bc2b-47501f10d921',
    '0295ceb3-125d-40b8-bda4-fa864465f423'
]

for inst_id in empty_ids:
    result = supabase.table("institutions").delete().eq("id", inst_id).execute()
    print(f"Deleted empty institution: {inst_id}")

print("\nCleanup complete!")
