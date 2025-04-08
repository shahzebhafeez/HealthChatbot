// Scroll to bottom of chat messages
function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Call scrollToBottom on page load
window.onload = scrollToBottom;

// Function to send message
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (message === '') return;
    
    // Clear input
    messageInput.value = '';
    
    // Add user message to chat
    const chatMessages = document.getElementById('chat-messages');
    const userMessageDiv = document.createElement('div');
    userMessageDiv.classList.add('message', 'user-message');
    userMessageDiv.textContent = message;
    chatMessages.appendChild(userMessageDiv);
    
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('loading');
    loadingDiv.innerHTML = '<div class="dot-flashing"></div>';
    chatMessages.appendChild(loadingDiv);
    
    scrollToBottom();
    
    // Send message to server
    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'message=' + encodeURIComponent(message)
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv);
        
        // Add assistant message
        const assistantMessageDiv = document.createElement('div');
        assistantMessageDiv.classList.add('message', 'assistant-message');
        assistantMessageDiv.textContent = data.message;
        chatMessages.appendChild(assistantMessageDiv);
        
        scrollToBottom();
    })
    .catch(error => {
        console.log('Error:', error);
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv);
        
        // Add error message
        const errorMessageDiv = document.createElement('div');
        errorMessageDiv.classList.add('message', 'assistant-message');
        errorMessageDiv.textContent = 'Sorry, there was an error processing your request.';
        chatMessages.appendChild(errorMessageDiv);
        
        scrollToBottom();
    });
}

// Send message on Enter key press
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});