const API_BASE_URL = "http://localhost:8000/api"; // This will be the Render URL in production

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Login Form Interceptor
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());
            
            try {
                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.status === "success") {
                    // Redirect on success
                    window.location.href = "/citizen/user_dashboard.html";
                } else {
                    alert(result.message || "Login failed");
                }
            } catch (err) {
                console.error("API Error:", err);
                alert("Failed to connect to backend");
            }
        });
    }

    // 2. Registration Form Interceptor
    const regForm = document.getElementById("regForm");
    if (regForm) {
        regForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            // Just sending dummy data since fields aren't strictly named in the mock
            const data = { docNo: "123", name: "Mock User" };
            
            try {
                const response = await fetch(`${API_BASE_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.status === "success") {
                    window.location.href = "/citizen/login_and_apply.html";
                }
            } catch (err) {
                console.error("API Error:", err);
            }
        });
    }

    // 3. Apply Income Form Interceptor
    const incomeForm = document.getElementById("incomeForm");
    if (incomeForm) {
        incomeForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const data = { purpose: "education" }; // Mock payload
            
            try {
                const response = await fetch(`${API_BASE_URL}/apply_income`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.status === "success") {
                    alert(`Application Submitted! ID: ${result.applicationId}`);
                    window.location.href = "/citizen/user_dashboard.html";
                }
            } catch (err) {
                console.error("API Error:", err);
            }
        });
    }

    // 4. Apply NCL Form Interceptor
    const nclForm = document.getElementById("nclForm");
    if (nclForm) {
        nclForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const data = { caste: "OBC" }; // Mock payload
            
            try {
                const response = await fetch(`${API_BASE_URL}/apply_ncl`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.status === "success") {
                    alert(`Application Submitted! ID: ${result.applicationId}`);
                    window.location.href = "/citizen/user_dashboard.html";
                }
            } catch (err) {
                console.error("API Error:", err);
            }
        });
    }
});
