from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="e-District Mock REST API")

# Allow CORS since frontend is on Vercel and backend is on Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegistrationData(BaseModel):
    docType: str = ""
    docNo: str = ""
    name: str = ""
    gender: str = ""
    dob: str = ""
    fatherName: str = ""
    motherName: str = ""
    houseNo: str = ""

class LoginData(BaseModel):
    userId: str = ""
    password: str = ""

class IncomeCertificateData(BaseModel):
    purpose: str = ""
    residence: str = ""
    issued_earlier: str = ""
    electricity: str = ""
    ration_card: str = ""
    tax_payee: str = ""
    school_fees: str = ""
    annual_income: str = ""

class NCLCertificateData(BaseModel):
    caste: str = ""
    state_origin: str = ""
    religion: str = ""
    creamy_layer: str = ""
    gov_emp: str = ""
    annual_income: str = ""
    wealth: str = ""

@app.get("/")
async def root():
    return {"status": "ok", "message": "e-District Clone API is running"}

@app.post("/api/register")
async def register(data: RegistrationData):
    return {"status": "success", "message": "User registered successfully", "userId": "mock_user_123"}

@app.post("/api/login")
async def login(data: LoginData):
    if data.userId and data.password:
        return {"status": "success", "token": "mock_jwt_token_12345"}
    return {"status": "error", "message": "Invalid credentials"}

@app.post("/api/apply_income")
async def apply_income(data: IncomeCertificateData):
    return {"status": "success", "applicationId": "INC-998877", "message": "Income certificate applied"}

@app.post("/api/apply_ncl")
async def apply_ncl(data: NCLCertificateData):
    return {"status": "success", "applicationId": "NCL-112233", "message": "NCL certificate applied"}
