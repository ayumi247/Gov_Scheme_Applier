document.addEventListener('DOMContentLoaded', () => {
    
    // Wizard State
    let currentStep = 1;
    const totalSteps = 3;
    
    // Elements
    const steps = {
        1: document.getElementById('step-1'),
        2: document.getElementById('step-2'),
        3: document.getElementById('step-3')
    };
    
    const indicators = {
        1: document.getElementById('indicator-1'),
        2: document.getElementById('indicator-2'),
        3: document.getElementById('indicator-3')
    };
    
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    if (!prevBtn) return;
    
    // URL Params for Scheme Name
    const urlParams = new URLSearchParams(window.location.search);
    const scheme = urlParams.get('scheme');
    if (scheme) {
        document.getElementById('schemeTitle').innerText = 'Apply for ' + (scheme === 'income' ? 'Income Certificate' : 'NCL Certificate');
    }
    
    function updateUI() {
        // Hide all
        Object.values(steps).forEach(el => el.classList.remove('active'));
        
        // Show current
        steps[currentStep].classList.add('active');
        
        // Update Indicators
        Object.keys(indicators).forEach(key => {
            if (parseInt(key) <= currentStep) {
                indicators[key].classList.add('active');
            } else {
                indicators[key].classList.remove('active');
            }
        });
        
        // Update Buttons
        prevBtn.style.display = currentStep > 1 ? 'block' : 'none';
        
        if (currentStep === totalSteps) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'block';
            
            // Populate Review Data
            document.getElementById('reviewName').innerText = document.getElementById('appName').value || 'Not provided';
            document.getElementById('reviewAadhar').innerText = document.getElementById('appAadhar').value || 'Not provided';
            document.getElementById('reviewPhone').innerText = document.getElementById('appPhone').value || 'Not provided';
        } else {
            nextBtn.style.display = 'block';
            submitBtn.style.display = 'none';
        }
    }
    
    nextBtn.addEventListener('click', () => {
        // Basic validation for Step 1
        if (currentStep === 1) {
            const form = document.getElementById('detailsForm');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
        }
        
        if (currentStep < totalSteps) {
            currentStep++;
            updateUI();
        }
    });
    
    prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep--;
            updateUI();
        }
    });
    
    submitBtn.addEventListener('click', () => {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = 'Processing... <i class="fa-solid fa-spinner fa-spin"></i>';
        submitBtn.disabled = true;
        
        // Mock API Submission Delay
        setTimeout(() => {
            alert('Application successfully handed over to the AI Agent! You can track its live status in your dashboard.');
            window.location.href = 'dashboard.html';
        }, 2000);
    });
    
    // Drag and Drop Logic
    const dropZone = document.getElementById('dropAadhar');
    const fileInput = document.getElementById('fileAadhar');
    const fileNameDisplay = document.getElementById('fileAadharName');
    
    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile(fileInput.files[0]);
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                handleFile(fileInput.files[0]);
            }
        });
        
        function handleFile(file) {
            fileNameDisplay.innerHTML = `<i class="fa-solid fa-check"></i> ${file.name} uploaded successfully`;
            dropZone.style.borderColor = 'var(--success)';
            dropZone.querySelector('i').className = 'fa-solid fa-file-circle-check';
            dropZone.querySelector('i').style.color = 'var(--success)';
        }
    }
});
