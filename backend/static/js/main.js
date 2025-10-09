document.addEventListener("DOMContentLoaded", function () {
    const navMobile = document.getElementById("navMobile");
    const toggleBtn = document.getElementById("mobileToggle");
    const overlay = document.getElementById("mobileOverlay");
    const toggleIcon = document.getElementById("toggleIcon");
    const body = document.body;
    
    function toggleMobileMenu() {
        const isOpen = navMobile.classList.contains("show");
        
        if (isOpen) {
            navMobile.classList.remove("show");
            overlay.classList.remove("show");
            body.classList.remove("menu-open");
            toggleIcon.textContent = "☰";
            toggleBtn.setAttribute("aria-label", "Abrir menú");
            toggleBtn.setAttribute("title", "Abrir menú de navegación");
        } else {
            navMobile.classList.add("show");
            overlay.classList.add("show");
            body.classList.add("menu-open");
            toggleIcon.textContent = "✕";
            toggleBtn.setAttribute("aria-label", "Cerrar menú");
            toggleBtn.setAttribute("title", "Cerrar menú de navegación");
        }
    }
    
    if (toggleBtn) {
        toggleBtn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMobileMenu();
        });
    }
    
    if (overlay) {
        overlay.addEventListener("click", function(e) {
            if (e.target === overlay) {
                toggleMobileMenu();
            }
        })
    }
    
    const mobileLinks = navMobile.querySelectorAll("a");
    mobileLinks.forEach(link => {
        link.addEventListener("click", function() {
            setTimeout(function() {
                if (navMobile.classList.contains("show")) {
                    toggleMobileMenu();
                }
            }, 150);
        });
    });
    
    window.addEventListener("resize", function() {
        if (window.innerWidth > 768) {
            navMobile.classList.remove("show");
            overlay.classList.remove("show");
            body.classList.remove("menu-open");
            toggleIcon.textContent = "☰";
            toggleBtn.setAttribute("aria-label", "Abrir menú");
            toggleBtn.setAttribute("title", "Abrir menú de navegación");
        }
    });
    
    document.addEventListener("keydown", function(e) {
        if (e.key === "Escape" && navMobile.classList.contains("show")) {
            toggleMobileMenu();
        }
    });
});