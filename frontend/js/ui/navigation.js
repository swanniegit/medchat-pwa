class NavigationUI {
    constructor() {
        this.currentPage = 'chat';
        this.pages = {};
        this.navItems = {};
        this.onPageChange = null;
    }

    init() {
        // Get all page elements
        this.pages = {
            chat: document.getElementById('chatContainer'),
            profile: document.getElementById('profileContainer'),
            edu: document.getElementById('eduContainer'),
            admin: document.getElementById('adminContainer')
        };

        // Get navigation items
        const navItems = document.querySelectorAll('[data-page]');
        navItems.forEach(item => {
            const page = item.getAttribute('data-page');
            this.navItems[page] = item;

            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPage(page);
            });
        });

        // Show initial page
        this.showPage(this.currentPage);
    }

    showPage(pageName) {
        if (!this.pages[pageName]) return;

        // Hide all pages
        Object.values(this.pages).forEach(page => {
            if (page) page.classList.remove('active');
        });

        // Remove active class from all nav items
        Object.values(this.navItems).forEach(item => {
            item.classList.remove('active');
        });

        // Show selected page
        this.pages[pageName].classList.add('active');
        if (this.navItems[pageName]) {
            this.navItems[pageName].classList.add('active');
        }

        this.currentPage = pageName;

        // Trigger page change callback
        if (this.onPageChange) {
            this.onPageChange(pageName);
        }
    }

    setPageChangeHandler(handler) {
        this.onPageChange = handler;
    }

    getCurrentPage() {
        return this.currentPage;
    }

    showAdminNav(show = true) {
        const adminNavItem = document.getElementById('adminNavItem');
        if (adminNavItem) {
            adminNavItem.style.display = show ? 'block' : 'none';
        }
    }
}

window.NavigationUI = NavigationUI;