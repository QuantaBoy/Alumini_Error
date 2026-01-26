document.addEventListener("DOMContentLoaded", () => {
    // ==============================
    // 1. SMART SCROLL ANIMATION
    // ==============================
    const navbar = document.querySelector(".navbar");
    const body = document.body;

    if (navbar) {
        window.addEventListener("scroll", () => {
            const scrollY = window.scrollY;

            // Navbar Transformation
            if (scrollY > 50) {
                navbar.classList.add("scrolled");
                body.classList.add("nav-scrolled");
            } else {
                navbar.classList.remove("scrolled");
                body.classList.remove("nav-scrolled");
            }
        });
    }

    // ==============================
    // 2. SMOOTH SCROLL TO TOP (If home icon present)
    // ==============================
    const homeIcon = document.querySelector("#home-icon");
    if (homeIcon) {
        homeIcon.addEventListener("click", (e) => {
            // If on profile page, home icon usually links to home, but if we want scroll behavior on home page, keep it.
            // Since this is profile page code, we might just let it be a link.
            // But if the user wants it to behave same way:
            // Check if href is # or current page
            const href = homeIcon.getAttribute('href');
            if (href === '#' || href === window.location.pathname) {
                e.preventDefault();
                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            }
        });
    }

    // ==============================
    // 3. SIDEBAR TOGGLE (Hamburger Menu)
    // ==============================
    const menuIcon = document.querySelector(".nav-menu-icon");
    // Note: Left panel might not exist on profile page, but we keep the listener safe
    const leftPanel = document.querySelector(".left-panel");

    if (menuIcon && leftPanel) {
        menuIcon.addEventListener("click", (e) => {
            e.stopPropagation();
            leftPanel.classList.toggle("active");
        });

        document.addEventListener("click", (e) => {
            if (leftPanel.classList.contains("active") &&
                !leftPanel.contains(e.target) &&
                !menuIcon.contains(e.target)) {
                leftPanel.classList.remove("active");
            }
        });
    }

    // ==============================
    // 4. PROFILE DROPDOWN TOGGLE
    // ==============================
    const profileContainer = document.getElementById("navProfileContainer");
    const profileDropdown = document.getElementById("profileDropdown");

    if (profileContainer && profileDropdown) {
        profileContainer.addEventListener("click", (e) => {
            e.stopPropagation();
            profileDropdown.classList.toggle("show");
        });

        // Close when clicking outside
        document.addEventListener("click", (e) => {
            if (!profileContainer.contains(e.target)) {
                profileDropdown.classList.remove("show");
            }
        });
    }
});
