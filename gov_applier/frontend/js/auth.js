// Initialize Supabase Client
const SUPABASE_URL = 'https://kqtoawziscqkbtlvvutr.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtxdG9hd3ppc2Nxa2J0bHZ2dXRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY0NzA0NDMsImV4cCI6MjEwMjA0NjQ0M30.UaozAXY72DErcH85FCn4DWMyV76gaOkfhiZGA_RptPY';

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
            
            // 1. Sign up user
            const { data, error } = await supabase.auth.signUp({
                email: email,
                password: password,
            });
            
            if (error) {
                alert('Registration failed: ' + error.message);
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
                return;
            }
            
            // 2. Insert into public.profiles
            if (data.user) {
                const { error: profileError } = await supabase
                    .from('profiles')
                    .insert([
                        { id: data.user.id, full_name: name }
                    ]);
                    
                if (profileError) {
                    console.error('Error creating profile:', profileError);
                }
            }
            
            alert('Account created! Please log in.');
            window.location.reload();
        });
    }
    
});
