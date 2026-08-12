import os
import tempfile
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

from src.orchestrator import run_dilli_saarthi_pipeline

load_dotenv()

app = FastAPI(title="Gov Scheme Automation Agent (CrewAI)")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret-key")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
E_DISTRICT_PORTAL_URL = os.getenv("E_DISTRICT_PORTAL_URL", "http://localhost:3000/clone/api")

class TriggerPayload(BaseModel):
    application_id: str

def process_application_task(application_id: str):
    """
    Background task that fetches data from Supabase and triggers the CrewAI Orchestrator.
    """
    print(f"Starting CrewAI automation for application: {application_id}")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Missing Supabase credentials in agent.")
        return
        
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # 1. Fetch Application Data
        res = supabase.table("applications").select("*").eq("id", application_id).single().execute()
        app_data = res.data
        if not app_data:
            print(f"Application {application_id} not found.")
            return
            
        extracted_info = app_data.get("extracted_data", {})
        
        user_profile = {
            "name": extracted_info.get("name", ""),
            "phone": extracted_info.get("phone", ""),
            "scheme_name": app_data.get("scheme_name", "unknown")
        }
        
        # 2. Download Document from Supabase Storage
        doc_paths = extracted_info.get("documents", [])
        temp_paths = {}
        
        for idx, storage_path in enumerate(doc_paths):
            doc_url = supabase.storage.from_("documents").get_public_url(storage_path)
            response = requests.get(doc_url)
            if response.status_code == 200:
                ext = storage_path.split('.')[-1] if '.' in storage_path else 'jpg'
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
                temp_file.write(response.content)
                temp_file.close()
                temp_paths[f"document_{idx}"] = temp_file.name
        
        # 3. Trigger CrewAI Pipeline
        print("Triggering Dilli-Saarthi CrewAI Pipeline...")
        result = run_dilli_saarthi_pipeline(
            user_profile=user_profile,
            document_paths=temp_paths,
            portal_url=f"{E_DISTRICT_PORTAL_URL}/apply_{user_profile['scheme_name']}"
        )
        
        # 4. Mark Application as Completed
        print(f"CrewAI Execution Finished. Result: {result.get('status')}")
        final_status = "completed" if result.get('status') == 'success' else "failed_automation"
        supabase.table("applications").update({"status": final_status}).eq("id", application_id).execute()
        
        # 5. Cleanup temp files
        for path in temp_paths.values():
            if os.path.exists(path):
                os.remove(path)
                
    except Exception as e:
        print(f"Error during CrewAI execution: {str(e)}")
        supabase.table("applications").update({"status": "failed_automation"}).eq("id", application_id).execute()

@app.get("/")
def health_check():
    return {"status": "CrewAI Agent is running and waiting for webhooks"}

@app.post("/trigger")
async def trigger_agent(
    payload: TriggerPayload, 
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(None)
):
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    background_tasks.add_task(process_application_task, payload.application_id)
    return {"status": "accepted", "message": f"CrewAI initialized for application {payload.application_id}"}
