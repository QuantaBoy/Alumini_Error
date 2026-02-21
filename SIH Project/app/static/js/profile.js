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
    // ==============================
    // 5. COVER PHOTO UPLOAD
    // ==============================
    const editCoverBtn = document.getElementById("editCoverBtn");
    const coverInput = document.getElementById("coverInput");
    const coverPhoto = document.getElementById("coverPhoto");

    // Restore saved cover on load
    const savedCover = localStorage.getItem("profile_cover_url");
    if (coverPhoto && savedCover) {
        coverPhoto.style.backgroundImage = `url('${savedCover}')`;
    }

    if (editCoverBtn && coverInput && coverPhoto) {
        editCoverBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            coverInput.click();
        });

        coverInput.addEventListener("change", async () => {
            const file = coverInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("cover", file);

            try {
                editCoverBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
                const res = await fetch("/api/upload-cover", {
                    method: "POST",
                    body: formData
                });

                if (!res.ok) throw new Error("Upload failed");

                const data = await res.json();
                coverPhoto.style.backgroundImage = `url('${data.url}')`;
                coverPhoto.style.backgroundSize = "cover";
                coverPhoto.style.backgroundPosition = "center";
                localStorage.setItem("profile_cover_url", data.url);
                editCoverBtn.innerHTML = '<i class="fas fa-camera"></i> Change Cover';
            } catch (err) {
                console.error("Cover upload error:", err);
                alert("Failed to upload cover photo.");
                editCoverBtn.innerHTML = '<i class="fas fa-camera"></i> Change Cover';
            }
        });
    }

    // ==============================
    // 6. AVATAR / PROFILE PHOTO UPLOAD
    // ==============================
    const changeAvatarBtn = document.getElementById("changeAvatarBtn");
    const avatarInput = document.getElementById("avatarInput");

    // Restore saved avatar on load
    const savedAvatar = localStorage.getItem("profile_avatar_url");
    if (savedAvatar) {
        const profileAvatar = document.getElementById("profileAvatarImg");
        if (profileAvatar) profileAvatar.src = savedAvatar;
        document.querySelectorAll(".nav-profile-img").forEach(img => img.src = savedAvatar);
    }

    if (changeAvatarBtn && avatarInput) {
        changeAvatarBtn.addEventListener("click", (e) => {
            e.preventDefault();
            avatarInput.click();
        });

        avatarInput.addEventListener("change", async () => {
            const file = avatarInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("avatar", file);

            try {
                changeAvatarBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
                const res = await fetch("/api/upload-avatar", {
                    method: "POST",
                    body: formData
                });

                if (!res.ok) throw new Error("Upload failed");

                const data = await res.json();

                // Update the main profile avatar and nav avatar
                const profileAvatar = document.getElementById("profileAvatarImg");
                if (profileAvatar) profileAvatar.src = data.url;
                document.querySelectorAll(".nav-profile-img").forEach(img => img.src = data.url);

                localStorage.setItem("profile_avatar_url", data.url);
                changeAvatarBtn.innerHTML = '<i class="fas fa-camera"></i> Change Photo';
            } catch (err) {
                console.error("Avatar upload error:", err);
                alert("Failed to upload profile photo.");
                changeAvatarBtn.innerHTML = '<i class="fas fa-camera"></i> Change Photo';
            }
        });
    }
});
