document.addEventListener("DOMContentLoaded", function () {
    const navMobile = document.getElementById("navMobile");
    const toggleBtn = document.getElementById("mobileToggle");
    const overlay = document.getElementById("mobileOverlay");
    const toggleIcon = document.getElementById("toggleIcon");
    const body = document.body;
    const userMenuToggle = document.getElementById('userMenuToggle');
    const userDropdown = document.getElementById('userDropdown');
    
    // Mobile menu
    function toggleMobileMenu() {
        const isOpen = navMobile.classList.contains("show");
        if (isOpen) {
            navMobile.classList.remove("show");
            overlay.classList.remove("show");
            body.classList.remove("menu-open");
            toggleIcon.textContent = "☰";
        } else {
            navMobile.classList.add("show");
            overlay.classList.add("show");
            body.classList.add("menu-open");
            toggleIcon.textContent = "✕";
        }
    }
    
    if (toggleBtn) {
        toggleBtn.addEventListener("click", toggleMobileMenu);
    }
    
    if (overlay) {
        overlay.addEventListener("click", toggleMobileMenu);
    }
    
    // User dropdown
    if (userMenuToggle) {
        userMenuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
            userMenuToggle.classList.toggle('active');
        });
    }
    
    document.addEventListener('click', function(event) {
        if (userDropdown && !userMenuToggle.contains(event.target) && !userDropdown.contains(event.target)) {
            userDropdown.classList.remove('show');
            userMenuToggle.classList.remove('active');
        }
    });
});