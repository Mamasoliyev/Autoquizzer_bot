// script.js - base.html uchun
document.addEventListener('DOMContentLoaded', () => {
    const currentUrl = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        }
    });
});
