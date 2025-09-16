class NightingaleChat {
    constructor() {
        this.userId = null;
        this.userName = null;
        this.department = null;

        // Initialize modular components
        this.websocketService = new WebSocketService();
        this.chatUI = null;
        this.navigationUI = new NavigationUI();
        this.profileUI = new ProfileUI();

        this.initElements();
        this.attachEventListeners();
        this.checkStoredUser();
        this.loadExistingProfile();
    }

    initElements() {
        this.loginScreen = document.getElementById('loginScreen');
        this.chatContainer = document.getElementById('chatContainer');
        this.loginForm = document.getElementById('loginForm');
        this.usernameInput = document.getElementById('username');
        this.departmentInput = document.getElementById('department');
        this.bioInput = document.getElementById('bio');
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.onlineCount = document.getElementById('onlineCount');

        // Initialize UI components
        this.chatUI = new ChatUI(this.messagesContainer, this.messageInput, this.sendBtn);
        this.chatUI.init();
        this.navigationUI.init();
        this.profileUI.init();

        // Set up UI event handlers
        this.chatUI.setSendHandler((text) => this.sendMessage(text));
        this.navigationUI.setPageChangeHandler((page) => this.onPageChanged(page));
    }

    attachEventListeners() {
        this.loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        // WebSocket event handlers
        this.websocketService.on('connected', () => {
            this.chatUI.updateConnectionStatus('Connected');
            Utils.showNotification('Connected to chat', 'success');
        });

        this.websocketService.on('disconnected', (data) => {
            this.chatUI.updateConnectionStatus('Disconnected');
            Utils.showNotification(`Disconnected: ${data.reason}`, 'warning');
        });

        this.websocketService.on('message', (data) => {
            this.handleMessage(data);
        });

        this.websocketService.on('error', (error) => {
            Utils.showNotification('Connection error', 'error');
        });

        this.websocketService.on('reconnectFailed', () => {
            Utils.showNotification('Failed to reconnect. Please refresh the page.', 'error');
        });

        // Install prompt handling
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });
    }

    checkStoredUser() {
        const userData = Utils.getUserData();
        if (userData) {
            this.userId = userData.userId;
            this.userName = userData.userName;
            this.department = userData.department;
            this.showChat();
            this.connectWebSocket();
        }
    }

    loadExistingProfile() {
        const userData = Utils.getUserData();
        if (userData) {
            this.usernameInput.value = userData.userName || '';
            this.departmentInput.value = userData.department || '';
            this.bioInput.value = userData.bio || '';
        }
    }

    login() {
        const username = this.usernameInput.value.trim();
        const department = this.departmentInput.value.trim();
        const bio = this.bioInput.value.trim();

        if (!Utils.validateInput(username, 100) || !Utils.validateInput(department, 100)) {
            Utils.showNotification('Please enter valid username and department', 'error');
            return;
        }

        this.userId = Utils.generateUserId();
        this.userName = username;
        this.department = department;

        const userData = {
            userId: this.userId,
            userName: this.userName,
            department: this.department,
            bio: bio
        };

        Utils.saveUserData(userData);
        this.chatUI.setCurrentUserId(this.userId);
        this.showChat();
        this.connectWebSocket();
    }

    showChat() {
        this.loginScreen.style.display = 'none';
        this.chatContainer.classList.add('active');
        document.getElementById('bottomNav').style.display = 'flex';
    }

    connectWebSocket() {
        this.websocketService.connect(this.userId)
            .then(() => {
                // Send initial user info
                this.websocketService.sendMessage({
                    type: 'user_info',
                    user_name: this.userName,
                    department: this.department,
                    bio: this.bioInput.value.trim()
                });
            })
            .catch((error) => {
                Utils.showNotification('Failed to connect to chat', 'error');
            });
    }

    sendMessage(text) {
        if (!Utils.validateInput(text)) return;

        const message = {
            type: 'message',
            text: Utils.sanitizeInput(text),
            user_name: this.userName,
            department: this.department,
            bio: this.bioInput.value.trim()
        };

        if (this.websocketService.sendMessage(message)) {
            // Add message to UI with "sending" status
            this.chatUI.addMessage({
                ...message,
                user_id: this.userId,
                timestamp: new Date().toISOString(),
                sending: true
            });
        } else {
            Utils.showNotification('Failed to send message. Check connection.', 'error');
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.chatUI.addMessage(data);
                break;
            case 'user_joined':
            case 'user_left':
                this.chatUI.addSystemMessage(data);
                break;
            case 'error':
                Utils.showNotification(data.message, 'error');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    onPageChanged(page) {
        // Handle page-specific logic
        if (page === 'admin') {
            this.loadAdminData();
        }
    }

    loadAdminData() {
        // Placeholder for admin functionality
        const onlineUsersCount = document.getElementById('onlineUsersCount');
        if (onlineUsersCount) {
            onlineUsersCount.textContent = 'Loading...';
        }
    }

    showInstallPrompt() {
        // PWA install prompt logic
        if (this.deferredPrompt) {
            Utils.showNotification('Install Nightingale-Chat for better experience!', 'info');
        }
    }

    logout() {
        Utils.clearUserData();
        this.websocketService.disconnect();
        location.reload();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.nightingaleChat = new NightingaleChat();
});