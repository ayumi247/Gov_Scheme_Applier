// Initialize Supabase Client
const SUPABASE_URL = 'https://kqtoawziscqkbtlvvutr.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_NTC1MTSfyIrR31IATdVlXQ_ivC7InVA';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    // Handle Login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            
            // UI Loading state
            const originalText = submitBtn.innerText;
            submitBtn.innerText = 'Logging in...';
            submitBtn.disabled = true;
            
            const { data, error } = await supabase.auth.signInWithPassword({
                email: email,
                password: password,
            });
            
            if (error) {
                alert('Login failed: ' + error.message);
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            } else {
                window.location.href = 'dashboard.html';
            }
        });
    }
    
    // Handle Registration
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            
            // UI Loading state
            const originalText = submitBtn.innerText;
            submitBtn.innerText = 'Creating account...';
            submitBtn.disabled = true;
            
            // 1. Sign up user with metadata
            const { data, error } = await supabase.auth.signUp({
                email: email,
                password: password,
                options: {
                    data: {
                        full_name: name
                    }
                }
            });
            
            if (error) {
                alert('Registration failed: ' + error.message);
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
                return;
            }
            
            // Profile insertion is now handled securely by Supabase Postgres Trigger
            
            alert('Account created! Please log in.');
            window.location.reload();
        });
    }
    
});
