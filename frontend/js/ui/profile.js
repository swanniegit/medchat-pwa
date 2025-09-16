class ProfileUI {
    constructor() {
        this.overlayAlert = null;
        this.overlayTitle = null;
        this.overlayMessage = null;
        this.overlayOkBtn = null;
    }

    init() {
        this.overlayAlert = document.getElementById('overlayAlert');
        this.overlayTitle = document.getElementById('overlayTitle');
        this.overlayMessage = document.getElementById('overlayMessage');
        this.overlayOkBtn = document.getElementById('overlayOkBtn');

        if (this.overlayOkBtn) {
            this.overlayOkBtn.addEventListener('click', () => {
                this.hideProfileOverlay();
            });
        }

        // Add click handlers for user profile cards
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('clickable-user')) {
                this.showUserProfile(e.target);
            }
        });
    }

    showUserProfile(element) {
        const name = element.getAttribute('data-name');
        const department = element.getAttribute('data-department');
        const bio = element.getAttribute('data-bio');

        if (name && department) {
            this.showProfileOverlay('User Profile', this.createProfileCard({
                name: name,
                department: department,
                bio: bio
            }));
        }
    }

    showProfileOverlay(title, content) {
        if (!this.overlayAlert) return;

        this.overlayTitle.textContent = title;
        this.overlayMessage.innerHTML = content;
        this.overlayAlert.classList.add('show');
    }

    hideProfileOverlay() {
        if (this.overlayAlert) {
            this.overlayAlert.classList.remove('show');
        }
    }

    createProfileCard(data) {
        const availabilityOptions = ['available', 'busy', 'away', 'offline'];
        const availability = availabilityOptions[Math.floor(Math.random() * availabilityOptions.length)];
        const availabilityText = availability.charAt(0).toUpperCase() + availability.slice(1);
        const availabilityClass = `availability-${availability}`;

        return `
            <div class="profile-card">
                <div class="profile-card-header">
                    <div class="profile-card-name">${data.name}</div>
                    <div class="profile-card-title">${data.title || 'Medical Professional'}</div>
                    <div class="profile-card-department">${data.department}${data.specialty ? ' • ' + data.specialty : ''}</div>
                </div>

                ${data.bio ? `
                <div class="profile-card-section">
                    <strong>About:</strong>
                    <p>${data.bio}</p>
                </div>
                ` : ''}

                <div class="profile-card-section">
                    <strong>Experience:</strong>
                    <p>${data.experience || '5+ years in healthcare'}</p>
                </div>

                <div class="profile-card-section">
                    <strong>Specialties:</strong>
                    <p>${data.specialties || 'Patient Care, Emergency Response'}</p>
                </div>

                <div class="profile-card-section">
                    <strong>Education:</strong>
                    <p>${data.education || 'Bachelor of Science in Nursing'}</p>
                </div>

                <div class="profile-card-section">
                    <strong>Certifications:</strong>
                    <p>${data.certifications || 'CPR, BLS, ACLS'}</p>
                </div>

                <div class="profile-card-section">
                    <strong>Availability:</strong>
                    <span class="availability-badge ${availabilityClass}">${availabilityText}</span>
                </div>
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

window.ProfileUI = ProfileUI;