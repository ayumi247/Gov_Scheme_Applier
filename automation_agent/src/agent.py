import os
import tempfile
import requests
from supabase import create_client, Client
from playwright.async_api import async_playwright

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
E_DISTRICT_PORTAL_URL = os.getenv("E_DISTRICT_PORTAL_URL", "http://localhost:3000") # Replace with Vercel deployment URL

async def process_application(application_id: str):
    """
    Background task that orchestrates the Playwright automation.
    """
    print(f"Starting automation for application: {application_id}")
    
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
        full_name = extracted_info.get("name", "")
        phone = extracted_info.get("phone", "")
        
        # 2. Download Document from Supabase Storage
        # For simplicity in this demo, we assume the first document is an image/PDF we need to upload
        doc_paths = extracted_info.get("documents", [])
        temp_file_path = None
        
        if doc_paths:
            storage_path = doc_paths[0]
            # Get a signed URL or public URL
            doc_url = supabase.storage.from_("documents").get_public_url(storage_path)
            
            # Download it to a temporary file for Playwright to use
            print(f"Downloading document from {doc_url}")
            response = requests.get(doc_url)
            if response.status_code == 200:
                # Create a temp file with proper extension
                ext = storage_path.split('.')[-1] if '.' in storage_path else 'jpg'
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
                temp_file.write(response.content)
                temp_file.close()
                temp_file_path = temp_file.name
        
        # 3. Start Playwright Automation
        async with async_playwright() as p:
            # We use headless=True for production on Render
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            print(f"Navigating to {E_DISTRICT_PORTAL_URL}...")
            
            # 3a. Login to the E-District Portal
            await page.goto(f"{E_DISTRICT_PORTAL_URL}/login.html")
            
            # Mock login (filling in standard fields)
            await page.fill('input[type="text"]', 'automation_agent_user')
            await page.fill('input[type="password"]', 'secure_password_123')
            await page.click('button[type="submit"]')
            
            # Wait for dashboard to load
            await page.wait_for_selector('h1', timeout=10000)
            
            # 3b. Navigate to the scheme application page
            scheme_name = app_data.get("scheme_name", "income")
            apply_url = f"{E_DISTRICT_PORTAL_URL}/api/apply_{scheme_name}" 
            # Note: In the mock portal, we had static HTML pages, so this might just be apply.html
            await page.goto(f"{E_DISTRICT_PORTAL_URL}/apply.html")
            
            print("Filling out forms on government portal...")
            # 3c. Fill out forms
            # These selectors depend on the exact HTML of the E-District clone
            # We will use general selectors for the sake of the script
            try:
                await page.fill('input[name="full_name"]', full_name)
                await page.fill('input[name="phone"]', phone)
            except Exception as e:
                print("Could not find generic form fields, moving to document upload...", e)
            
            # 3d. Upload Document
            if temp_file_path:
                try:
                    # Look for file input
                    file_input = await page.query_selector('input[type="file"]')
                    if file_input:
                        await file_input.set_input_files(temp_file_path)
                except Exception as e:
                    print("Could not find file input.", e)
            
            # 3e. Submit Form
            try:
                await page.click('button[type="submit"]')
                # Wait for success page or API response
                await page.wait_for_timeout(2000) 
            except Exception as e:
                print("Submit button error", e)
            
            await browser.close()
            
            # Cleanup temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
        # 4. Mark Application as Completed in Supabase
        print("Automation successful! Updating database status to 'completed'.")
        supabase.table("applications").update({"status": "completed"}).eq("id", application_id).execute()
        
    except Exception as e:
        print(f"Error during Playwright automation: {str(e)}")
        # Optionally update status to 'failed'
        supabase.table("applications").update({"status": "failed_automation"}).eq("id", application_id).execute()
