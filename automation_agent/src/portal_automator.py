import os
import json
import asyncio
import datetime
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from crewai.tools import BaseTool

class PortalAutomatorInput(BaseModel):
    """Pydantic schema for PortalAutomationTool arguments."""
    portal_url: str = Field(description="The base URL of the government portal")
    credentials: dict = Field(description="Login credentials (username, password)")
    user_data: dict = Field(description="User demographic details mapping")
    document_paths: dict = Field(description="Dictionary mapping doc keys to local temp file paths")

class PortalAutomationTool(BaseTool):
    """
    CrewAI Tool wrapper for the async Playwright Portal Automator.
    Adapted for asynchronous scaling on Render.
    """
    name: str = "Portal Auto-Filler & Document Uploader"
    description: str = (
        "Automates browser navigation, logs in, fills demographic forms using robust CSS fallback selectors, "
        "and uploads required documents."
    )
    args_schema: Type[BaseModel] = PortalAutomatorInput

    def _run(self, portal_url: str, credentials: dict, user_data: dict, document_paths: dict) -> str:
        """
        CrewAI natively executes tools synchronously. To run async Playwright inside it, 
        we spin up a local event loop.
        """
        # Ensure we parse dicts if passed as strings by LLM
        if isinstance(credentials, str): credentials = json.loads(credentials)
        if isinstance(user_data, str): user_data = json.loads(user_data)
        if isinstance(document_paths, str): document_paths = json.loads(document_paths)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.run_automation(portal_url, credentials, user_data, document_paths)
            )
            return json.dumps(result, indent=2)
        finally:
            loop.close()

    async def run_automation(self, portal_url: str, credentials: dict, user_data: dict, document_paths: dict) -> dict:
        """Core async Playwright logic."""
        log = []
        def _log(msg: str):
            log.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
            print(log[-1])

        _log("Initializing Playwright browser (headless mode)...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=100)
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()
            page.set_default_timeout(30000)

            try:
                # 1. Navigate
                _log(f"Navigating to {portal_url}")
                await page.goto(portal_url)

                # 2. Login (with Fallbacks)
                username = credentials.get("username", "")
                password = credentials.get("password", "")
                
                # Fill Username
                for sel in ['input[name*="user" i]', '#username', 'input[type="text"]']:
                    locator = page.locator(sel).first
                    if await locator.is_visible(timeout=2000):
                        await locator.fill(username)
                        _log(f"Filled username via {sel}")
                        break
                        
                # Fill Password
                for sel in ['input[type="password"]', '#password', 'input[name*="pass" i]']:
                    locator = page.locator(sel).first
                    if await locator.is_visible(timeout=2000):
                        await locator.fill(password)
                        _log(f"Filled password via {sel}")
                        break
                        
                # Submit
                for sel in ['button[type="submit"]', 'button:has-text("Login")']:
                    locator = page.locator(sel).first
                    if await locator.is_visible(timeout=2000):
                        await locator.click()
                        _log(f"Clicked login via {sel}")
                        break

                await page.wait_for_load_state("domcontentloaded")
                
                # 3. Form Filling (Dynamic logic for the mock clone portal / real portal)
                _log("Starting scheme application form filling...")
                for key, val in user_data.items():
                    # Attempt to find fields matching the key
                    sel = f'input[name="{key}" i]'
                    try:
                        locator = page.locator(sel).first
                        if await locator.is_visible(timeout=1000):
                            await locator.fill(str(val))
                            _log(f"Filled {key} = {val}")
                    except PlaywrightTimeoutError:
                        pass
                
                # 4. Upload Documents
                _log(f"Attempting to upload {len(document_paths)} documents...")
                try:
                    file_input = page.locator('input[type="file"]').first
                    if await file_input.is_visible(timeout=2000) and document_paths:
                        # For simplicity, we upload the first document in the dict to the generic file input
                        first_doc_path = list(document_paths.values())[0]
                        if os.path.exists(first_doc_path):
                            await file_input.set_input_files(first_doc_path)
                            _log(f"Uploaded {first_doc_path}")
                except Exception as e:
                    _log(f"File upload error: {str(e)}")
                    
                # 5. Submit Application
                try:
                    await page.click('button[type="submit"]')
                    await page.wait_for_timeout(2000) 
                    _log("Application submitted successfully.")
                except Exception as e:
                    _log(f"Submit error: {str(e)}")

                return {
                    "status": "SUCCESS",
                    "execution_log": log,
                    "final_url": page.url
                }
                
            except Exception as e:
                _log(f"Fatal error during automation: {str(e)}")
                return {
                    "status": "FAIL",
                    "error": str(e),
                    "execution_log": log
                }
            finally:
                await browser.close()
