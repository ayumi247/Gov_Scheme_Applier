document.addEventListener('DOMContentLoaded', () => {
    
    const toggleBtn = document.getElementById('chatbotToggle');
    const closeBtn = document.getElementById('chatbotClose');
    const panel = document.getElementById('chatbotPanel');
    const form = document.getElementById('chatbotForm');
    const input = document.getElementById('chatbotInput');
    const messagesContainer = document.getElementById('chatbotMessages');
    
    if (!toggleBtn || !panel) return;
    
    // Toggle Chat Panel
    toggleBtn.addEventListener('click', () => {
        panel.classList.toggle('open');
    });
    
    closeBtn.addEventListener('click', () => {
        panel.classList.remove('open');
    });
    
    // Add Message to UI
    function addMessage(text, sender) {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender);
        bubble.innerText = text;
        messagesContainer.appendChild(bubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Handle Chat Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const userMsg = input.value.trim();
        if (!userMsg) return;
        
        // 1. Show User Message
        addMessage(userMsg, 'user');
        input.value = '';
        
        // 2. Show typing indicator (mock)
        const typingBubble = document.createElement('div');
        typingBubble.classList.add('chat-bubble', 'bot');
        typingBubble.innerHTML = '<i class="fa-solid fa-ellipsis"></i>';
        messagesContainer.appendChild(typingBubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        try {
            // 3. Call our Backend which securely uses the Grok API
            // Guardrail logic is handled in the backend system prompt.
            /* 
               System Prompt for Backend:
               "You are Grok, an AI assistant for the Gov Scheme Applier platform. 
               You MUST ONLY answer questions related to government schemes, scholarships, and the e-district portal application process. 
               If the user asks about ANY other topic (coding, politics, general knowledge), politely decline and remind them of your purpose."
            */
            
            // Mock API Call for now until Phase 4 Backend is ready
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Remove typing indicator
            typingBubble.remove();
            
            // Basic frontend guardrail check (for demo purposes)
            const lowerMsg = userMsg.toLowerCase();
            if (lowerMsg.includes('scheme') || lowerMsg.includes('apply') || lowerMsg.includes('document') || lowerMsg.includes('scholarship')) {
                addMessage("I can definitely help with that! To apply for that scheme, you will need to upload your Aadhar Card and Income proof in the 'New Application' wizard.", 'bot');
            } else {
                addMessage("I am a specialized AI. I can only assist you with questions regarding government schemes and the e-District portal. Please ask me a related question!", 'bot');
            }
            
        } catch (err) {
            typingBubble.remove();
            addMessage("Sorry, I am having trouble connecting to Grok right now.", 'bot');
        }
    });
});
