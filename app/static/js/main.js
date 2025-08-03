document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather Icons
    feather.replace();

    // Simple animations on scroll for elements with 'wow' class
    const wowElements = document.querySelectorAll('.wow');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    wowElements.forEach(el => {
        observer.observe(el);
    });

    // Close flash messages
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(message) {
        const closeButton = message.querySelector('.close');
        if(closeButton) {
            closeButton.addEventListener('click', function() {
                message.style.display = 'none';
            });
        }
    });
});
