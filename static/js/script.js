document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearHistoryButton = document.createElement('button');
    clearHistoryButton.textContent = 'Clear History';
    clearHistoryButton.id = 'clear-history-button';
    document.querySelector('.input-container').appendChild(clearHistoryButton);

    function addMessage(message, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'bot-message');
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, true);
            userInput.value = '';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message }),
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                const data = await response.json();
                addMessage(data.response, false);
            } catch (error) {
                console.error('Error:', error);
                addMessage('Sorry, there was an error processing your request.', false);
            }
        }
    }

    async function fetchConversationHistory() {
        try {
            const response = await fetch('/history');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            chatMessages.innerHTML = '';
            data.history.forEach(msg => {
                addMessage(msg.content, msg.role === 'user');
            });
        } catch (error) {
            console.error('Error fetching conversation history:', error);
        }
    }

    async function clearConversationHistory() {
        try {
            const response = await fetch('/clear_history', { method: 'POST' });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            chatMessages.innerHTML = '';
            addMessage('Conversation history has been cleared.', false);
        } catch (error) {
            console.error('Error clearing conversation history:', error);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    clearHistoryButton.addEventListener('click', clearConversationHistory);

    // Fetch conversation history when the page loads
    fetchConversationHistory();
});
