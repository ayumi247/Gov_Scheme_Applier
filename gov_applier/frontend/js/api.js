// Centralized API handler for calls to the Render FastAPI backend
// This will be fully implemented in Phase 4.

const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalhost ? 'http://localhost:8000' : 'https://gov-scheme-main-backend.onrender.com';

const API = {
    
    async fetchSchemes() {
        console.log('Fetching schemes from backend...');
        // Mock returning data
        return [
            { id: 'income', name: 'Income Certificate' },
            { id: 'ncl', name: 'NCL Certificate' }
        ];
    },
    
    async submitApplication(applicationData) {
        console.log('Sending application to Agent API...', applicationData);
        // This will call the FastAPI endpoint which triggers the Agent
        return { success: true, tracking_id: 'APP-2026-XYZ' };
    }
};

window.GovApplierAPI = API;
