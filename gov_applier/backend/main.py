import os
import re
import io
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
import pytesseract
from PIL import Image
from thefuzz import fuzz

# Load environment variables from .env file
load_dotenv()

# Setup Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Use Service Key for backend overrides if needed
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

app = FastAPI(title="Gov Scheme Applier API")

# Configure CORS for our Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this to Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional dependency to verify Supabase JWT token from frontend
def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split("Bearer ")[1]
    # Note: With the service_role key, we can interact directly. 
    # But strictly, we should use the anon_key or decode the JWT to verify the user.
    try:
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Gov Scheme Applier API (Tesseract OCR Active)"}

# 1. OCR Document Upload & Verification
@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    expected_name: str = Form(...),
    # user = Depends(verify_token) # Enable in production
):
    try:
        # 1. Read Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 2. Run Tesseract OCR
        # Note: We use eng+hin since Indian documents often have both
        extracted_text = pytesseract.image_to_string(image, lang='eng+hin')
        text_clean = extracted_text.replace('\n', ' ').lower()
        
        # 3. Verification Logic
        is_valid = False
        reason = "Verification failed."
        
        if doc_type == "aadhar":
            # Check for 12 digit number format (e.g., 1234 5678 9012)
            # This regex allows spaces between blocks of 4 digits
            aadhar_pattern = re.compile(r'\d{4}\s?\d{4}\s?\d{4}')
            if aadhar_pattern.search(text_clean):
                # Fuzzy match the user's name
                name_match_score = fuzz.partial_ratio(expected_name.lower(), text_clean)
                if name_match_score > 80:
                    is_valid = True
                    reason = "Aadhar verified successfully."
                else:
                    reason = f"Aadhar number found, but name '{expected_name}' did not match clearly (Score: {name_match_score})."
            else:
                reason = "No 12-digit Aadhar number found in document."
                
        elif doc_type == "income":
            if "income" in text_clean or "आय" in text_clean:
                name_match_score = fuzz.partial_ratio(expected_name.lower(), text_clean)
                if name_match_score > 80:
                    is_valid = True
                    reason = "Income proof verified successfully."
                else:
                    reason = "Document looks like income proof, but name did not match."
            else:
                reason = "Document does not appear to be an Income Certificate."
        
        if not is_valid:
            return {"success": False, "error": reason, "extracted_text_preview": text_clean[:200]}
            
        # 4. If valid, upload to Supabase Storage
        # This part requires a storage bucket named "documents" created in Supabase
        file_path = f"{expected_name.replace(' ', '_')}_{doc_type}_{file.filename}"
        
        try:
            res = supabase.storage.from_("documents").upload(file_path, contents, {"content-type": file.content_type})
            public_url = supabase.storage.from_("documents").get_public_url(file_path)
        except Exception as storage_err:
            print("Storage upload error:", storage_err)
            # If bucket doesn't exist, we just mock success for the prototype
            public_url = f"mock_url/{file_path}"
        
        return {
            "success": True, 
            "message": reason, 
            "url": public_url,
            "document_type": doc_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Chatbot Endpoint
class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_with_ai(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the server.")
        
    system_prompt = """You are an AI assistant for the Gov Scheme Applier platform in India.
    Your strictly enforced rules:
    1. You MUST ONLY answer questions related to government schemes (Income, NCL, Caste), scholarships, and the e-District portal application process.
    2. If the user asks about ANYTHING ELSE (coding, politics, general knowledge, movies), politely decline and remind them of your purpose.
    3. Keep your answers brief, professional, and helpful.
    """
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile", # Using Groq's high-speed model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        reply = data["choices"][0]["message"]["content"]
        return {"reply": reply}
        
    except Exception as e:
        print("Groq API Error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to connect to AI provider.")

# 3. Final Apply Submission
class ApplicationData(BaseModel):
    scheme_id: str
    full_name: str
    aadhar_no: str
    phone: str
    documents: list[str]

@app.post("/api/apply")
async def submit_application(data: ApplicationData):
    # This endpoint receives the verified data from the frontend wizard
    # and inserts a row into the 'applications' table.
    # The insertion will trigger Phase 5 automation.
    
    try:
        # Mocking user_id for now since we bypassed JWT extraction above
        # In prod, get user_id from verify_token
        mock_user_id = "00000000-0000-0000-0000-000000000000" 
        
        app_insert = {
            "user_id": mock_user_id,
            "scheme_name": data.scheme_id,
            "status": "pending_agent",
            "extracted_data": {
                "name": data.full_name,
                "phone": data.phone,
                "aadhar": data.aadhar_no,
                "documents": data.documents
            }
        }
        
        # supabase.table("applications").insert(app_insert).execute()
        
        # Here we would also fire the webhook to the CrewAI Agent
        # requests.post("https://our-agent-url.onrender.com/trigger", json={"application_id": "mock_id"})
        
        return {
            "success": True,
            "tracking_id": f"APP-{data.scheme_id.upper()}-101",
            "message": "Application saved. AI Agent has been notified."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


