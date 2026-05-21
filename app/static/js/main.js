document.addEventListener('DOMContentLoaded', () => {
    console.log("AECC Web Portal Initialized.");
    
    // Highlight active link in navigation menu
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath.startsWith('/admin') && href.startsWith('/admin'))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Auto-dismiss alert messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }
});
