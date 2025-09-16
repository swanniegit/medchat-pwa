class NightingaleChat {
    constructor() {
        this.socket = null;
        this.userId = null;
        this.userName = null;
        this.department = null;
        this.isConnected = false;

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

        // Navigation elements
        this.bottomNav = document.getElementById('bottomNav');
        this.pages = {
            chat: document.getElementById('chatContainer'),
            profile: document.getElementById('profileContainer'),
            edu: document.getElementById('eduContainer'),
            admin: document.getElementById('adminContainer')
        };

        // Overlay elements
        this.overlayAlert = document.getElementById('overlayAlert');
        this.overlayTitle = document.getElementById('overlayTitle');
        this.overlayMessage = document.getElementById('overlayMessage');
        this.overlayOkBtn = document.getElementById('overlayOkBtn');

        // Admin elements
        this.adminNavItem = document.getElementById('adminNavItem');
        this.alertForm = document.getElementById('alertForm');
        this.alertTitle = document.getElementById('alertTitle');
        this.alertMessage = document.getElementById('alertMessage');
        this.alertTarget = document.getElementById('alertTarget');
        this.previewAlert = document.getElementById('previewAlert');
        this.onlineUsersCount = document.getElementById('onlineUsersCount');

        // Profile elements
        this.profileForm = document.getElementById('profileForm');
        this.profileName = document.getElementById('profileName');
        this.profileTitle = document.getElementById('profileTitle');
        this.profileDepartment = document.getElementById('profileDepartment');
        this.profileSpecialty = document.getElementById('profileSpecialty');
        this.profileQualifications = document.getElementById('profileQualifications');
        this.profileExperience = document.getElementById('profileExperience');
        this.profileLanguages = document.getElementById('profileLanguages');
        this.profileLocation = document.getElementById('profileLocation');
        this.profilePhone = document.getElementById('profilePhone');
        this.profileEmail = document.getElementById('profileEmail');
        this.profileBio = document.getElementById('profileBio');
        this.profileAvailability = document.getElementById('profileAvailability');
        this.previewProfile = document.getElementById('previewProfile');
        this.profilePreview = document.getElementById('profilePreview');
        this.profileCard = document.getElementById('profileCard');
        this.bioCharCount = document.getElementById('bioCharCount');
    }

    attachEventListeners() {
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // PWA install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });

        // Navigation event listeners
        this.bottomNav.addEventListener('click', (e) => {
            const navItem = e.target.closest('.nav-item');
            if (navItem) {
                const page = navItem.dataset.page;
                this.switchPage(page);
            }
        });

        // Overlay event listeners
        this.overlayOkBtn.addEventListener('click', () => this.hideOverlay());
        this.overlayAlert.addEventListener('click', (e) => {
            if (e.target === this.overlayAlert) {
                this.hideOverlay();
            }
        });

        // Admin event listeners
        this.alertForm.addEventListener('submit', (e) => this.handleSendAlert(e));
        this.previewAlert.addEventListener('click', () => this.handlePreviewAlert());

        // Profile event listeners
        this.profileForm.addEventListener('submit', (e) => this.handleSaveProfile(e));
        this.previewProfile.addEventListener('click', () => this.handlePreviewProfile());
        this.profileBio.addEventListener('input', () => this.updateCharCount());
    }

    checkStoredUser() {
        const storedUser = localStorage.getItem('medchat_user');
        if (storedUser) {
            const userData = JSON.parse(storedUser);
            this.usernameInput.value = userData.name;
            this.departmentInput.value = userData.department;
            this.bioInput.value = userData.bio || '';
        }
    }

    async handleLogin(e) {
        console.log('Login form submitted');
        e.preventDefault();

        const username = this.usernameInput.value.trim();
        const department = this.departmentInput.value.trim();
        const bio = this.bioInput.value.trim();

        console.log('Form values:', { username, department, bio });

        // Validate inputs
        if (!this.validateInput(username, 'username')) {
            console.log('Username validation failed:', username);
            alert('Invalid username. Use only letters, numbers, spaces, hyphens, and underscores (1-50 chars).');
            return;
        }

        if (!this.validateInput(department, 'department')) {
            console.log('Department validation failed:', department);
            alert('Invalid department. Use only letters, numbers, spaces, hyphens, and underscores (1-50 chars).');
            return;
        }

        // Sanitize inputs
        const sanitizedUsername = this.sanitizeInput(username, 50);
        const sanitizedDepartment = this.sanitizeInput(department, 50);
        const sanitizedBio = this.sanitizeInput(bio, 200);

        this.userName = username;
        this.department = department;
        this.bio = bio || '';
        this.userId = this.generateUserId();

        // Check for admin access (simple check for demo)
        this.isAdmin = (username.toLowerCase() === 'admin' || department.toLowerCase() === 'admin');
        if (this.isAdmin) {
            this.adminNavItem.style.display = 'flex';
        }

        // Store user data
        localStorage.setItem('medchat_user', JSON.stringify({
            name: username,
            department: department,
            bio: bio
        }));

        await this.connectWebSocket();
    }

    switchPage(pageName) {
        // Hide all pages
        Object.values(this.pages).forEach(page => {
            page.classList.remove('active');
        });

        // Show selected page
        if (this.pages[pageName]) {
            this.pages[pageName].classList.add('active');
        }

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

        // Hide bottom nav and header on login screen
        if (this.loginScreen.style.display !== 'none') {
            this.bottomNav.style.display = 'none';
            document.querySelector('.header').style.display = 'none';
        } else {
            this.bottomNav.style.display = 'flex';
            document.querySelector('.header').style.display = 'flex';
        }
    }

    generateUserId() {
        return `${this.userName.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`;
    }

    async connectWebSocket() {
        const wsUrl = this.getWebSocketUrl();
        console.log('🔗 Attempting WebSocket connection to:', wsUrl);

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log('✅ WebSocket connected successfully');
                this.isConnected = true;
                this.updateConnectionStatus('Connected', true);
                this.showChatInterface();
                this.fetchOnlineUsers();
            };

            this.socket.onmessage = (event) => {
                console.log('📨 Message received:', event.data);
                const message = JSON.parse(event.data);
                this.handleIncomingMessage(message);
            };

            this.socket.onclose = (event) => {
                console.log('🔌 WebSocket closed:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus('Disconnected', false);
                setTimeout(() => this.reconnect(), 3000);
            };

            this.socket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.updateConnectionStatus('Connection Error', false);
            };

        } catch (error) {
            console.error('❌ Connection failed:', error);
            this.updateConnectionStatus('Failed to Connect', false);
        }
    }

    reconnect() {
        if (!this.isConnected && this.userId) {
            this.updateConnectionStatus('Reconnecting...', false);
            this.connectWebSocket();
        }
    }

    showChatInterface() {
        this.loginScreen.style.display = 'none';
        document.querySelector('.header').style.display = 'flex';
        this.bottomNav.style.display = 'flex';

        // Show chat page by default
        this.switchPage('chat');
        this.messageInput.focus();
    }

    updateConnectionStatus(status, isConnected) {
        this.connectionStatus.textContent = status;
        this.connectionStatus.style.color = isConnected ? '#fff' : '#ffcccb';
    }

    async fetchOnlineUsers() {
        try {
            const apiUrl = this.getApiUrl();
            const response = await fetch(`${apiUrl}/users/online`);
            const data = await response.json();
            this.onlineCount.textContent = `${data.count} online`;

            // Update admin stats if admin page exists
            if (this.onlineUsersCount) {
                this.onlineUsersCount.textContent = data.count;
            }
        } catch (error) {
            console.error('Failed to fetch online users:', error);
        }
    }

    handleIncomingMessage(message) {
        switch (message.type) {
            case 'user_joined':
            case 'user_left':
                this.addSystemMessage(message.message);
                this.fetchOnlineUsers();
                break;
            default:
                this.addMessage(message, false);
                break;
        }
    }

    sendMessage() {
        const text = this.messageInput.value.trim();

        if (!this.isConnected) {
            alert('Not connected to chat server. Please wait or refresh the page.');
            return;
        }

        if (!this.validateInput(text, 'message')) {
            alert('Message is too long (max 1000 characters) or empty.');
            return;
        }

        const sanitizedText = this.sanitizeInput(text, 1000);

        const message = {
            type: 'message',
            user_id: this.userId,
            user_name: this.sanitizeInput(this.userName, 50),
            department: this.sanitizeInput(this.department, 50),
            bio: this.sanitizeInput(this.bio, 200),
            text: sanitizedText
        };

        // Add message to UI immediately (optimistic update)
        this.addMessage(message, true);

        // Send via WebSocket
        this.socket.send(JSON.stringify(message));

        // Clear input
        this.messageInput.value = '';
    }

    addMessage(message, isOwn) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwn ? 'own' : ''}`;

        const time = message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${!isOwn ? `<div class="message-sender clickable-user" data-bio="${this.escapeHtml(message.bio || '')}" data-name="${message.user_name}" data-department="${message.department}">${message.user_name} • ${message.department}</div>` : ''}
                <div class="message-text">${this.escapeHtml(message.text)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        // Add click event for bio popup
        if (!isOwn && message.bio) {
            const senderElement = messageDiv.querySelector('.clickable-user');
            senderElement.addEventListener('click', () => this.showUserBio(message));
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addSystemMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.textContent = text;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showInstallPrompt() {
        // Create install banner (simplified for POC)
        if (this.deferredPrompt) {
            setTimeout(() => {
                if (confirm('Install Nightingale-Chat as an app for better experience?')) {
                    this.deferredPrompt.prompt();
                }
            }, 5000);
        }
    }

    showUserBio(message) {
        const bioText = message.bio || 'No bio available';
        alert(`👨‍⚕️ ${message.user_name}\n📋 ${message.department}\n\n📝 Bio:\n${bioText}`);
    }

    // Security utilities
    sanitizeInput(input, maxLength = 1000) {
        if (!input) return '';

        // Remove potential XSS
        let sanitized = input.toString()
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');

        // Limit length
        sanitized = sanitized.slice(0, maxLength);

        return sanitized.trim();
    }

    validateInput(input, type = 'text') {
        if (!input) return false;

        switch (type) {
            case 'username':
                return /^[a-zA-Z0-9_\s-]{1,50}$/.test(input);
            case 'department':
                return /^[a-zA-Z0-9_\s-]{1,50}$/.test(input);
            case 'message':
                return input.length > 0 && input.length <= 1000;
            case 'email':
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
            case 'phone':
                return /^\+?[\d\s\-\(\)]{1,20}$/.test(input);
            default:
                return input.length <= 1000;
        }
    }

    // Update WebSocket URL for HTTPS
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = '8000';
        return `${protocol}//${host}:${port}/ws/${this.userId}`;
    }

    // Get API URL matching current protocol
    getApiUrl() {
        const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
        const host = window.location.hostname;
        const port = '8000';
        return `${protocol}//${host}:${port}`;
    }

    // Overlay Alert Methods
    showOverlay(title, message) {
        this.overlayTitle.textContent = title;
        this.overlayMessage.textContent = message;
        this.overlayAlert.classList.add('show');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    hideOverlay() {
        this.overlayAlert.classList.remove('show');
        document.body.style.overflow = ''; // Restore scrolling
    }

    // Promotional Alert Methods
    showPromoAlert(title = "🎉 Special Announcement", message = "Welcome to Nightingale-Chat! Your professional medical network.") {
        this.showOverlay(title, message);
    }

    // Admin Alert Methods
    handlePreviewAlert() {
        const title = this.alertTitle.value.trim();
        const message = this.alertMessage.value.trim();

        if (!title || !message) {
            alert('Please fill in both title and message fields.');
            return;
        }

        this.showOverlay(title, message);
    }

    handleSendAlert(e) {
        e.preventDefault();

        const title = this.alertTitle.value.trim();
        const message = this.alertMessage.value.trim();
        const target = this.alertTarget.value;

        if (!title || !message) {
            alert('Please fill in both title and message fields.');
            return;
        }

        // For now, just show the alert locally (in real app, this would go through WebSocket)
        this.showOverlay(title, message);

        // Clear the form
        this.alertForm.reset();

        // Show success message
        setTimeout(() => {
            this.hideOverlay();
            alert(`✅ Alert sent successfully to ${target === 'all' ? 'all users' : target}!`);
        }, 2000);
    }

    // Profile Form Methods
    updateCharCount() {
        const text = this.profileBio.value;
        const count = text.length;
        this.bioCharCount.textContent = count;

        // Change color based on limit
        if (count > 450) {
            this.bioCharCount.style.color = '#e74c3c';
        } else if (count > 400) {
            this.bioCharCount.style.color = '#f39c12';
        } else {
            this.bioCharCount.style.color = '#666';
        }

        // Enforce limit
        if (count > 500) {
            this.profileBio.value = text.slice(0, 500);
            this.bioCharCount.textContent = '500';
        }
    }

    handlePreviewProfile() {
        const profileData = this.getProfileFormData();

        if (!this.validateRequiredFields(profileData)) {
            alert('Please fill in all required fields (marked with *)');
            return;
        }

        this.generateProfilePreview(profileData);
        this.profilePreview.style.display = 'block';

        // Scroll to preview
        this.profilePreview.scrollIntoView({ behavior: 'smooth' });
    }

    handleSaveProfile(e) {
        e.preventDefault();

        const profileData = this.getProfileFormData();

        if (!this.validateRequiredFields(profileData)) {
            alert('Please fill in all required fields (marked with *)');
            return;
        }

        // Save to localStorage
        localStorage.setItem('nightingale_profile', JSON.stringify(profileData));

        // Show success message
        this.showOverlay(
            "✅ Profile Saved!",
            "Your professional profile has been saved successfully. Other medical professionals can now discover and connect with you."
        );

        // Update basic bio in user data
        const userData = JSON.parse(localStorage.getItem('medchat_user') || '{}');
        userData.bio = profileData.bio;
        localStorage.setItem('medchat_user', JSON.stringify(userData));
    }

    getProfileFormData() {
        return {
            name: this.profileName.value.trim(),
            title: this.profileTitle.value.trim(),
            department: this.profileDepartment.value,
            specialty: this.profileSpecialty.value.trim(),
            qualifications: this.profileQualifications.value.trim(),
            experience: this.profileExperience.value,
            languages: this.profileLanguages.value.trim(),
            location: this.profileLocation.value.trim(),
            phone: this.profilePhone.value.trim(),
            email: this.profileEmail.value.trim(),
            bio: this.profileBio.value.trim(),
            availability: this.profileAvailability.value
        };
    }

    validateRequiredFields(data) {
        return data.name && data.title && data.department && data.location;
    }

    generateProfilePreview(data) {
        const availabilityClass = `availability-${data.availability}`;
        const availabilityText = {
            'available': 'Available for consultation',
            'limited': 'Limited availability',
            'unavailable': 'Not available'
        }[data.availability] || 'Available for consultation';

        this.profileCard.innerHTML = `
            <div class="profile-card-header">
                <div class="profile-card-name">${data.name}</div>
                <div class="profile-card-title">${data.title}</div>
                <div class="profile-card-department">${data.department}${data.specialty ? ' • ' + data.specialty : ''}</div>
            </div>

            ${data.qualifications ? `
            <div class="profile-card-section">
                <h4>🎓 Qualifications & Certifications</h4>
                <p>${data.qualifications}</p>
            </div>
            ` : ''}

            <div class="profile-card-section">
                <h4>💼 Experience & Skills</h4>
                ${data.experience ? `<p><strong>Experience:</strong> ${data.experience}</p>` : ''}
                ${data.languages ? `<p><strong>Languages:</strong> ${data.languages}</p>` : ''}
            </div>

            <div class="profile-card-section">
                <h4>📍 Location & Contact</h4>
                <p><strong>Location:</strong> ${data.location}</p>
                ${data.phone ? `<p><strong>Phone:</strong> ${data.phone}</p>` : ''}
                ${data.email ? `<p><strong>Email:</strong> ${data.email}</p>` : ''}
            </div>

            ${data.bio ? `
            <div class="profile-card-section">
                <h4>📋 Professional Bio</h4>
                <p>${data.bio}</p>
            </div>
            ` : ''}

            <div class="profile-card-section">
                <h4>🕒 Availability</h4>
                <span class="availability-badge ${availabilityClass}">${availabilityText}</span>
            </div>
        `;
    }

    loadExistingProfile() {
        const savedProfile = localStorage.getItem('nightingale_profile');
        if (savedProfile) {
            const data = JSON.parse(savedProfile);

            // Populate form fields
            this.profileName.value = data.name || '';
            this.profileTitle.value = data.title || '';
            this.profileDepartment.value = data.department || '';
            this.profileSpecialty.value = data.specialty || '';
            this.profileQualifications.value = data.qualifications || '';
            this.profileExperience.value = data.experience || '';
            this.profileLanguages.value = data.languages || '';
            this.profileLocation.value = data.location || '';
            this.profilePhone.value = data.phone || '';
            this.profileEmail.value = data.email || '';
            this.profileBio.value = data.bio || '';
            this.profileAvailability.value = data.availability || 'available';

            this.updateCharCount();
        }
    }
}

// Register service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
        .then(registration => console.log('SW registered:', registration))
        .catch(error => console.log('SW registration failed:', error));
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.nightingaleApp = new NightingaleChat();
});