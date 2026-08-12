# 🏛️ Gov Scheme Applier & Multi-Agent Automation Platform

Welcome to the **Gov Scheme Applier** repository! This is a state-of-the-art, multi-agent web application designed to bridge the gap between citizens and government schemes. 

By combining a beautiful modern frontend, a robust FastAPI backend, and an intelligent **CrewAI** multi-agent automation system, this platform allows users to apply for complex government schemes through a simple conversational interface, while AI agents handle the heavy lifting of interacting with legacy government portals in the background.

---

## 🚀 Architecture Overview

This project is built using a highly scalable, decoupled microservices architecture designed for cloud deployment on **Vercel** and **Render**.

The repository is structured into four main components:

### 1. Main Website Frontend (`gov_applier/frontend/`)
The beautiful, user-facing web interface where citizens interact with the AI chatbot to determine their eligibility and submit their details.
- **Tech Stack:** HTML5, CSS3 (Glassmorphism), Vanilla JavaScript.
- **Deployment:** Vercel.

### 2. Main Website Backend (`gov_applier/backend/`)
The primary REST API that powers the frontend. It handles secure user authentication, fetches scheme details from the database, powers the RAG-based AI chatbot, and securely triggers the automation agent.
- **Tech Stack:** Python, FastAPI, Supabase (PostgreSQL), Groq API (LLM).
- **Deployment:** Render (Web Service 1).

### 3. CrewAI Automation Agent (`automation_agent/`)
The heavy-duty, asynchronous worker service. Once a user submits an application, this service receives a webhook, downloads the user's documents from Supabase, validates them using OCR, and deploys autonomous Playwright agents to navigate and fill out the legacy government portal.
- **Tech Stack:** Python, CrewAI, Playwright, Tesseract OCR.
- **Deployment:** Render (Web Service 2).

### 4. e-District Clone Backend (`e-district_clone/backend/`)
A standalone, lightweight mock API that perfectly simulates a real government e-District portal. It allows the CrewAI agents to practice and execute web automation safely without hitting real government servers during testing.
- **Tech Stack:** Python, FastAPI.
- **Deployment:** Render (Web Service 3).

---

## ⚙️ CI/CD Pipeline

This project features a fully automated Continuous Integration and Continuous Deployment (CI/CD) pipeline via **GitHub Actions** (`.github/workflows/main.yml`).

Upon every push to the `main` branch:
1. **Testing:** The pipeline spins up an Ubuntu runner, installs Tesseract OCR, and executes `pytest` across the backend and agent modules.
2. **Deployment:** If all tests pass, the pipeline automatically triggers deployment webhooks to push the latest code to Render and Vercel simultaneously.

---

## 🛠️ Local Development Setup

To run this massive ecosystem locally, you will need to set up environment variables for the different services.

### Prerequisites
- Python 3.11+
- Tesseract OCR installed on your system.
- A **Supabase** account (for Postgres DB & Storage).
- A **Groq** account (for ultra-fast LLM inference).

### Setting up the Environment
Create a `.env` file in `gov_applier/backend/` and `automation_agent/` with the following variables:
```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
WEBHOOK_SECRET=your_secure_password
```

### Running the Services
You can spin up any of the FastAPI servers locally using Uvicorn. For example, to run the Main Backend:
```bash
cd gov_applier/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## 🛡️ Security Note
This repository contains a master `.gitignore` file that ensures no API keys, virtual environments, or `__pycache__` folders are ever pushed to the public repository. **Never commit your `.env` files.**
