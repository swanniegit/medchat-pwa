class ChatUI {
    constructor(messageContainer, messageInput, sendButton) {
        this.messageContainer = messageContainer;
        this.messageInput = messageInput;
        this.sendButton = sendButton;
        this.messages = [];
        this.onSendMessage = null;
    }

    init() {
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        this.messageInput.addEventListener('input', () => {
            this.sendButton.disabled = !this.messageInput.value.trim();
        });
    }

    sendMessage() {
        const text = this.messageInput.value.trim();
        if (text && this.onSendMessage) {
            this.onSendMessage(text);
            this.messageInput.value = '';
            this.sendButton.disabled = true;
        }
    }

    addMessage(message) {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messageDiv = document.createElement('div');
        const isOwn = message.user_id === this.currentUserId;
        const time = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageDiv.className = `message ${isOwn ? 'own' : ''}`;
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${!isOwn ? `<div class="message-sender clickable-user" data-bio="${this.escapeHtml(message.bio || '')}" data-name="${message.user_name}" data-department="${message.department}">${message.user_name} • ${message.department}</div>` : ''}
                <div class="message-text">${this.escapeHtml(message.text)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        this.messageContainer.appendChild(messageDiv);
    }

    addSystemMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.innerHTML = `
            <div class="system-text">
                ${this.escapeHtml(message.message)}
            </div>
        `;
        this.messageContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setCurrentUserId(userId) {
        this.currentUserId = userId;
    }

    setSendHandler(handler) {
        this.onSendMessage = handler;
    }

    updateConnectionStatus(status) {
        // Implementation for connection status updates
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = status === 'Connected' ? 'status-connected' : 'status-disconnected';
        }
    }
}

window.ChatUI = ChatUI;