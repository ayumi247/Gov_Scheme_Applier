import os
import json
import traceback
from typing import Dict, Type
from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq

from src.rag_engine import SchemeResearchTool
from src.doc_validator import DocumentAuditor
from src.portal_automator import PortalAutomationTool

# Tool wrapper for Document Auditor
class DocumentAuditorInput(BaseModel):
    document_paths: dict = Field(description="Dictionary mapping doc keys to local temp file paths")

class DocumentAuditorTool(BaseTool):
    name: str = "Document OCR & Quality Auditor"
    description: str = "Audits uploaded user documents for constraints, blurriness, and text extraction using Tesseract OCR."
    args_schema: Type[BaseModel] = DocumentAuditorInput

    def _run(self, document_paths: dict) -> str:
        if isinstance(document_paths, str): document_paths = json.loads(document_paths)
        audit_results = {}
        all_passed = True
        
        for key, path in document_paths.items():
            res = DocumentAuditor.run_full_audit(path)
            audit_results[key] = res
            if res.get("audit_status") != "PASS":
                all_passed = False
                
        status = "PASS" if all_passed and document_paths else "FAIL"
        return json.dumps({
            "overall_status": status,
            "documents": audit_results
        }, indent=2)

def run_dilli_saarthi_pipeline(user_profile: dict, document_paths: dict, portal_url: str) -> dict:
    """
    Executes the 3-agent CrewAI pipeline.
    """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY")
    )

    policy_researcher = Agent(
        role="Scheme Eligibility Analyst",
        goal="Determine if the user is eligible for the requested scheme.",
        backstory="An expert in Delhi welfare rules.",
        tools=[SchemeResearchTool()],
        llm=llm,
        verbose=True
    )

    compliance_auditor = Agent(
        role="Document Validation Inspector",
        goal="Ensure uploaded files are clear, valid, and not expired using Tesseract.",
        backstory="A strict compliance inspector.",
        tools=[DocumentAuditorTool()],
        llm=llm,
        verbose=True
    )

    web_executor = Agent(
        role="Portal Automation Specialist",
        goal="Automate portal navigation and form filling using async Playwright.",
        backstory="A browser automation specialist executing submissions securely.",
        tools=[PortalAutomationTool()],
        llm=llm,
        verbose=True
    )

    task1 = Task(
        description=f"Analyze eligibility for profile: {json.dumps(user_profile)}.",
        expected_output="JSON containing eligibility status.",
        agent=policy_researcher
    )

    task2 = Task(
        description=f"Audit the following documents: {json.dumps(document_paths)}.",
        expected_output="JSON with overall_status and per-document breakdown.",
        agent=compliance_auditor
    )

    task3 = Task(
        description=(
            f"If the auditor returned PASS, call the Portal Auto-Filler with "
            f"portal_url='{portal_url}', credentials={{'username': 'mock_user'}}, "
            f"user_data={json.dumps(user_profile)}, and document_paths={json.dumps(document_paths)}. "
            f"If FAIL, return SKIPPED."
        ),
        expected_output="JSON with execution status.",
        agent=web_executor,
        context=[task2]
    )

    crew = Crew(
        agents=[policy_researcher, compliance_auditor, web_executor],
        tasks=[task1, task2, task3],
        process=Process.sequential,
        verbose=True
    )

    try:
        crew.kickoff()
        return {"status": "success", "message": "Pipeline completed."}
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
