import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# LangChain / RAG Imports
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# CrewAI Imports
from crewai.tools import BaseTool

class EligibilityResult(BaseModel):
    """Structured output for the LLM eligibility check."""
    is_eligible: bool = Field(description="True if the user is eligible for any scheme, else False")
    confidence_score: float = Field(description="Confidence score of the eligibility determination (0.0 to 1.0)")
    matched_schemes: List[str] = Field(description="List of scheme names the user is eligible for")
    eligibility_reasoning: str = Field(description="Detailed explanation explaining why they are or aren't eligible")
    required_documents_checklist: List[str] = Field(description="List of mandatory certificates or documents needed to apply")

class SchemeKnowledgeEngine:
    """
    Local RAG Engine for indexing government circulars and reasoning about eligibility.
    Adapted for Groq API.
    """
    def __init__(self, index_path: str = "./faiss_index"):
        self.index_path = index_path
        # Lightweight CPU embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None
        self.groq_api_key = os.getenv("GROQ_API_KEY")

    def build_index(self, pdf_dir_or_path: str) -> None:
        """Ingests PDF documents, chunks them, and builds a local FAISS vector index."""
        print(f"Loading documents from: {pdf_dir_or_path}")
        docs = []
        if os.path.isfile(pdf_dir_or_path) and pdf_dir_or_path.lower().endswith(".pdf"):
            loader = PyMuPDFLoader(pdf_dir_or_path)
            docs.extend(loader.load())
        elif os.path.isdir(pdf_dir_or_path):
            for file in os.listdir(pdf_dir_or_path):
                if file.lower().endswith(".pdf"):
                    loader = PyMuPDFLoader(os.path.join(pdf_dir_or_path, file))
                    docs.extend(loader.load())
        else:
            raise ValueError(f"Invalid path provided: {pdf_dir_or_path}")

        if not docs:
            print("No PDF documents found to index.")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(docs)

        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        self.vector_store.save_local(self.index_path)

    def load_index(self) -> bool:
        """Loads the FAISS index if it exists."""
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
            return True
        return False

    def check_eligibility(self, user_query: str, user_profile: Optional[Dict[str, Any]] = None) -> dict:
        """Queries the vector database and uses Groq to determine eligibility based on retrieved context."""
        if self.vector_store is None:
            if not self.load_index():
                raise FileNotFoundError(f"FAISS index not found at {self.index_path}. Please build it first.")

        # Similarity Search
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        relevant_docs = retriever.invoke(user_query)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # Initialize Groq LLM
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set.")
            
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_retries=2,
            api_key=self.groq_api_key
        )
        
        structured_llm = llm.with_structured_output(EligibilityResult)

        prompt_template = """
        You are an expert Government Scheme Eligibility Advisor.
        Your task is to analyze the user's query and profile against the provided official government circular context.

        Context from Official Documents:
        {context}

        User Profile:
        {user_profile}

        User Query:
        {user_query}

        Based strictly on the provided Context and User Profile, determine the user's eligibility.
        List any mandatory documents they will need.
        """

        prompt = PromptTemplate(
            input_variables=["context", "user_profile", "user_query"],
            template=prompt_template
        )

        formatted_prompt = prompt.format(
            context=context,
            user_profile=json.dumps(user_profile) if user_profile else "Not provided",
            user_query=user_query
        )

        try:
            result = structured_llm.invoke(formatted_prompt)
            return result.dict()
        except Exception as e:
            return {
                "error": str(e),
                "is_eligible": False,
                "confidence_score": 0.0,
                "matched_schemes": [],
                "eligibility_reasoning": f"Error parsing response: {str(e)}",
                "required_documents_checklist": []
            }

class SchemeResearchTool(BaseTool):
    """
    CrewAI Tool wrapper for the SchemeKnowledgeEngine.
    """
    name: str = "Government Scheme Eligibility Researcher"
    description: str = (
        "Use this tool to search through government circulars and determine if a citizen "
        "is eligible for specific schemes. Input must be a descriptive query."
    )
    
    engine: SchemeKnowledgeEngine = Field(default_factory=SchemeKnowledgeEngine)

    def _run(self, query: str) -> str:
        try:
            result_dict = self.engine.check_eligibility(user_query=query)
            return json.dumps(result_dict, indent=2)
        except Exception as e:
            return f"Error executing eligibility check: {str(e)}"
