document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const settingsButton = document.getElementById('settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const closeButton = document.querySelector('.close');
    const settingsForm = document.getElementById('settings-form');
    
    // Chat settings
    let chatSettings = {
        modelName: 'llama3:8b',
        collectionName: 'documents',
        keywordPromptPath: './prompts/keyword_extractor.md',
        contextPromptPath: './prompts/context_based_query.md',
        serviceType: 'ollama',
        numChunks: 10,
        displayContext: false
    };
    
    // Initialize responder when the page loads
    initializeResponder();
    
    // Auto-resize the textarea as the user types
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });
    
    // Send message when the send button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Send message when Enter key is pressed (but allow Shift+Enter for new lines)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Open settings modal
    settingsButton.addEventListener('click', () => {
        // Update form values with current settings
        document.getElementById('model-name').value = chatSettings.modelName;
        document.getElementById('collection-name').value = chatSettings.collectionName;
        document.getElementById('keyword-prompt-path').value = chatSettings.keywordPromptPath;
        document.getElementById('context-prompt-path').value = chatSettings.contextPromptPath;
        document.getElementById('service-type').value = chatSettings.serviceType;
        document.getElementById('num-chunks').value = chatSettings.numChunks;
        document.getElementById('display-context').checked = chatSettings.displayContext;
        
        settingsModal.style.display = 'block';
    });
    
    // Close settings modal
    closeButton.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
    
    // Save settings and initialize responder
    settingsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Update settings from form values
        chatSettings.modelName = document.getElementById('model-name').value;
        chatSettings.collectionName = document.getElementById('collection-name').value;
        chatSettings.keywordPromptPath = document.getElementById('keyword-prompt-path').value;
        chatSettings.contextPromptPath = document.getElementById('context-prompt-path').value;
        chatSettings.serviceType = document.getElementById('service-type').value;
        chatSettings.numChunks = parseInt(document.getElementById('num-chunks').value);
        chatSettings.displayContext = document.getElementById('display-context').checked;
        
        // Initialize responder with new settings
        initializeResponder();
        
        // Close modal
        settingsModal.style.display = 'none';
        
        // Add system message
        addMessage('system', `Settings updated. Using model: ${chatSettings.modelName} with service: ${chatSettings.serviceType}`);
    });
    
    function initializeResponder() {
        // Get the base URL
        const baseUrl = window.location.origin;
        
        // Send initialization request to the API
        fetch(`${baseUrl}/api/initialize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: chatSettings.modelName,
                collection_name: chatSettings.collectionName,
                keyword_prompt_path: chatSettings.keywordPromptPath,
                context_prompt_path: chatSettings.contextPromptPath,
                service_type: chatSettings.serviceType
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Responder initialized:', data);
        })
        .catch(error => {
            console.error('Error initializing responder:', error);
            addMessage('system', `Error initializing responder: ${error.message}. Using default settings.`);
        });
    }
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to the chat
        addMessage('user', message);
        
        // Clear the input field and reset its height
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Get the base URL
        const baseUrl = window.location.origin;
        
        // Send the message to the API
        fetch(`${baseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                num_chunks: chatSettings.numChunks,
                display_context: chatSettings.displayContext
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add assistant response to the chat
            if (data.error) {
                addMessage('assistant', `Error: ${data.error}`);
            } else if (data.context && chatSettings.displayContext) {
                // If display_context is true and we have context, show both
                addMessage('assistant', data.response);
                addMessage('system', `<strong>Context used:</strong><br>${formatContext(data.context)}`);
            } else {
                addMessage('assistant', data.response);
            }
        })
        .catch(error => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add error message to the chat
            addMessage('assistant', `Sorry, there was an error processing your request: ${error.message}`);
        });
    }
    
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Process markdown-like formatting for code blocks
        const formattedContent = formatMessage(content);
        messageContent.innerHTML = formattedContent;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingContent.appendChild(dot);
        }
        
        typingDiv.appendChild(typingContent);
        chatMessages.appendChild(typingDiv);
        
        // Scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingDiv;
    }
    
    function formatMessage(text) {
        // Convert URLs to clickable links
        text = text.replace(/https?:\/\/[^\s]+/g, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
        
        // Convert code blocks (```code```) to <pre><code> elements
        text = text.replace(/```([\s\S]*?)```/g, (match, code) => {
            return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
        });
        
        // Convert inline code (`code`) to <code> elements
        text = text.replace(/`([^`]+)`/g, (match, code) => {
            return `<code>${escapeHtml(code)}</code>`;
        });
        
        // Convert line breaks to <br> tags
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    function formatContext(context) {
        // Truncate context if it's too long
        if (context.length > 1000) {
            context = context.substring(0, 1000) + '... (truncated)';
        }
        return escapeHtml(context).replace(/\n/g, '<br>');
    }
    
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
