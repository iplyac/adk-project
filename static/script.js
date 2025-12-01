// Configuration for different environments
const CONFIG = {
    // Local development
    local: {
        apiUrl: 'http://localhost:8000'
    },
    // Docker local
    docker: {
        apiUrl: 'http://localhost:8080'
    },
    // Cloud Run production
    production: {
        apiUrl: 'https://adk-agent-298607833444.us-central1.run.app'
    }
};

// Auto-detect environment or set manually
const ENVIRONMENT = window.location.hostname === 'localhost'
    ? (window.location.port === '8080' ? 'docker' : 'local')
    : 'production';

const API_URL = CONFIG[ENVIRONMENT].apiUrl;

console.log(`Environment: ${ENVIRONMENT}, API URL: ${API_URL}`);

// Rest of your existing script.js code...
// Just replace hardcoded URLs with API_URL variable

const sessionId = 'session_' + Math.random().toString(36).substring(7);

async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const message = chatInput.value.trim();

    if (!message) return;

    // Disable input while processing
    chatInput.disabled = true;
    sendBtn.disabled = true;

    // Add user message to chat
    appendMessage(message, 'user');
    chatInput.value = '';

    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        const data = await response.json();
        appendMessage(data.response, 'agent');

        // Refresh stats immediately to show new request count
        updateDashboard();

    } catch (error) {
        console.error('Error sending message:', error);
        appendMessage('Error: Could not send message.', 'agent');
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function appendMessage(text, sender) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = text;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function updateDashboard() {
    try {
        // Fetch health
        const healthResponse = await fetch(`${API_URL}/health`);
        const healthData = await healthResponse.json();
        document.getElementById('status').textContent = healthData.status;
        document.getElementById('uptime').textContent = Math.floor(healthData.uptime_seconds) + 's';

        // Fetch stats
        const statsResponse = await fetch(`${API_URL}/stats`);
        const statsData = await statsResponse.json();
        document.getElementById('request-count').textContent = statsData.request_count;
        document.getElementById('error-count').textContent = statsData.error_count;
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

// Event listeners
document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initial dashboard update
updateDashboard();
setInterval(updateDashboard, 5000); // Update every 5 seconds
