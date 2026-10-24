// ==========================================================================
// HouseRent Professional Platform JavaScript
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss alert banners after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Show / Hide Password toggle
    const toggleBtns = document.querySelectorAll(".password-toggle-btn");
    toggleBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            const targetId = btn.getAttribute("data-target") || "password";
            const input = document.getElementById(targetId);
            const icon = btn.querySelector("i");
            if (input) {
                if (input.type === "password") {
                    input.type = "text";
                    if (icon) {
                        icon.classList.remove("bi-eye");
                        icon.classList.add("bi-eye-slash");
                    }
                } else {
                    input.type = "password";
                    if (icon) {
                        icon.classList.remove("bi-eye-slash");
                        icon.classList.add("bi-eye");
                    }
                }
            }
        });
    });

    // Confirmation dialog for deletion and destructive operations
    const confirmForms = document.querySelectorAll(".delete-confirm-form");
    confirmForms.forEach(function (form) {
        form.addEventListener("submit", function (e) {
            const message = form.getAttribute("data-confirm-message") || 
                "Are you sure you want to permanently delete this record? This action cannot be undone.";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Image preview helper for property file uploads
    const imageInput = document.getElementById("image_file");
    const previewContainer = document.getElementById("image_preview_container");
    const previewImg = document.getElementById("image_preview");

    if (imageInput && previewContainer && previewImg) {
        imageInput.addEventListener("change", function () {
            const file = imageInput.files[0];
            if (file) {
                // Check size limit: 5MB
                if (file.size > 5 * 1024 * 1024) {
                    alert("Selected file is larger than 5MB limit. Please choose a smaller image.");
                    imageInput.value = "";
                    previewContainer.classList.add("d-none");
                    return;
                }
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImg.src = e.target.result;
                    previewContainer.classList.remove("d-none");
                };
                reader.readAsDataURL(file);
            } else {
                previewContainer.classList.add("d-none");
            }
        });
    }
});
