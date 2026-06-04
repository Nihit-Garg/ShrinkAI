import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv
import httpx

load_dotenv()
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

async def test():
    # Login as an existing user or sign up
    print("Trying to sign up/in...")
    res = supabase.auth.sign_up({"email": "test12345@example.com", "password": "password123!"})
    if not res.user:
        res = supabase.auth.sign_in_with_password({"email": "test12345@example.com", "password": "password123!"})
    
    token = res.session.access_token
    print("Token fetched. Calling API...")
    
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:8000/questionnaire/status", headers={"Authorization": f"Bearer {token}"})
        print(r.status_code)
        print(r.text)

asyncio.run(test())
