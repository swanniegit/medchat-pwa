class Utils {
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static generateUserId() {
        return Math.random().toString(36).substr(2, 9);
    }

    static formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static validateInput(text, maxLength = 1000) {
        return text && text.trim().length > 0 && text.trim().length <= maxLength;
    }

    static sanitizeInput(text) {
        return text.trim().substring(0, 1000);
    }

    static showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    static getUserData() {
        const stored = localStorage.getItem('nightingale_user');
        return stored ? JSON.parse(stored) : null;
    }

    static saveUserData(userData) {
        localStorage.setItem('nightingale_user', JSON.stringify(userData));
    }

    static clearUserData() {
        localStorage.removeItem('nightingale_user');
    }
}

window.Utils = Utils;