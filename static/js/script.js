/* =========================================================
   ROOMFINDER - MAIN JAVASCRIPT
   Professional UI interactions
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    "use strict";


    /* =====================================================
       INITIALIZATION
    ===================================================== */

    console.log("RoomFinder JavaScript loaded successfully.");


    /* =====================================================
       BUTTON LOADING STATE
       Automatically works with form submit buttons
    ===================================================== */

    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const submitButton =
                form.querySelector(
                    'button[type="submit"]:not([data-no-loading])'
                );

            if (!submitButton) {
                return;
            }

            /*
             * Don't disable buttons that are meant to submit
             * multiple times or have special behavior.
             */

            if (form.dataset.noLoading === "true") {
                return;
            }


            /*
             * Small delay so browser can actually submit
             * the form normally.
             */

            submitButton.disabled = true;

            submitButton.classList.add("button-loading");


            const originalHTML =
                submitButton.innerHTML;


            submitButton.dataset.originalHTML =
                originalHTML;


            submitButton.innerHTML = `
                <span
                    class="spinner-border spinner-border-sm me-2"
                    aria-hidden="true"
                ></span>
                Please wait...
            `;

        });

    });


    /* =====================================================
       DELETE / DANGER CONFIRMATION
       Use:
       data-confirm="Delete this property?"
       ===================================================== */

    const confirmationElements =
        document.querySelectorAll("[data-confirm]");


    confirmationElements.forEach(function (element) {

        element.addEventListener("click", function (event) {

            const message =
                element.dataset.confirm ||
                "Are you sure you want to continue?";


            const confirmed =
                window.confirm(message);


            if (!confirmed) {

                event.preventDefault();

                event.stopPropagation();

            }

        });

    });


    /* =====================================================
       FAVORITE BUTTON
       Adds a small visual feedback
       ===================================================== */

    const favoriteForms =
        document.querySelectorAll(
            'form[action*="favorite"]'
        );


    favoriteForms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const button =
                form.querySelector("button");


            if (!button) {
                return;
            }


            button.disabled = true;

            button.classList.add(
                "button-loading"
            );


            button.innerHTML = `
                <span
                    class="spinner-border spinner-border-sm me-2"
                    aria-hidden="true"
                ></span>
                Updating...
            `;

        });

    });


    /* =====================================================
       IMAGE PREVIEW
       Automatically works with:
       <input type="file" accept="image/*">
       ===================================================== */

    const imageInputs =
        document.querySelectorAll(
            'input[type="file"][accept*="image"]'
        );


    imageInputs.forEach(function (input) {

        input.addEventListener("change", function () {

            const files =
                Array.from(input.files || []);


            if (!files.length) {
                return;
            }


            /*
             * Find an existing preview container.
             */

            let preview =
                document.querySelector(
                    "[data-image-preview]"
                );


            /*
             * If preview doesn't exist,
             * create one automatically.
             */

            if (!preview) {

                preview =
                    document.createElement("div");

                preview.dataset.imagePreview = "true";

                preview.className =
                    "image-preview-container";

                input.parentElement.appendChild(
                    preview
                );

            }


            preview.innerHTML = "";


            files.forEach(function (file) {

                if (!file.type.startsWith("image/")) {
                    return;
                }


                const reader =
                    new FileReader();


                reader.onload = function (event) {

                    const wrapper =
                        document.createElement("div");

                    wrapper.className =
                        "image-preview-item";


                    const image =
                        document.createElement("img");

                    image.src =
                        event.target.result;

                    image.alt =
                        "Selected property image";


                    wrapper.appendChild(image);

                    preview.appendChild(wrapper);

                };


                reader.readAsDataURL(file);

            });

        });

    });


    /* =====================================================
       PASSWORD SHOW / HIDE
       
       Works with:
       data-password-toggle
       ===================================================== */

    const passwordToggles =
        document.querySelectorAll(
            "[data-password-toggle]"
        );


    passwordToggles.forEach(function (toggle) {

        toggle.addEventListener("click", function () {

            const targetId =
                toggle.dataset.passwordToggle;


            const passwordInput =
                document.getElementById(targetId);


            if (!passwordInput) {
                return;
            }


            if (passwordInput.type === "password") {

                passwordInput.type = "text";


                toggle.innerHTML =
                    '<i class="bi bi-eye-slash"></i>';

                toggle.setAttribute(
                    "aria-label",
                    "Hide password"
                );

            }

            else {

                passwordInput.type = "password";


                toggle.innerHTML =
                    '<i class="bi bi-eye"></i>';

                toggle.setAttribute(
                    "aria-label",
                    "Show password"
                );

            }

        });

    });


    /* =====================================================
       AUTO DISMISS FLASH ALERTS
       Bootstrap alerts with:
       data-auto-dismiss
       ===================================================== */

    const alerts =
        document.querySelectorAll(
            '[data-auto-dismiss="true"]'
        );


    alerts.forEach(function (alert) {

        setTimeout(function () {

            if (
                typeof bootstrap !== "undefined"
            ) {

                const alertInstance =
                    bootstrap.Alert.getOrCreateInstance(
                        alert
                    );

                alertInstance.close();

            }

            else {

                alert.remove();

            }

        }, 5000);

    });


    /* =====================================================
       SEARCH FORM UX
       Prevent negative rent values
       ===================================================== */

    const rentInputs =
        document.querySelectorAll(
            'input[name="min_rent"], input[name="max_rent"], input[name="rent"]'
        );


    rentInputs.forEach(function (input) {

        input.addEventListener("input", function () {

            if (Number(input.value) < 0) {

                input.value = 0;

            }

        });

    });


    /* =====================================================
       MIN / MAX RENT VALIDATION
       ===================================================== */

    const searchForms =
        document.querySelectorAll(
            'form[method="GET"]'
        );


    searchForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const minInput =
                form.querySelector(
                    '[name="min_rent"]'
                );


            const maxInput =
                form.querySelector(
                    '[name="max_rent"]'
                );


            if (
                !minInput ||
                !maxInput ||
                !minInput.value ||
                !maxInput.value
            ) {

                return;

            }


            const min =
                Number(minInput.value);


            const max =
                Number(maxInput.value);


            if (min > max) {

                event.preventDefault();


                showRoomFinderMessage(
                    "Minimum rent cannot be greater than maximum rent.",
                    "warning"
                );


                minInput.focus();

            }

        });

    });


    /* =====================================================
       SMOOTH SCROLL
       Works for:
       <a href="#section">
       ===================================================== */

    const anchorLinks =
        document.querySelectorAll(
            'a[href^="#"]'
        );


    anchorLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            const targetId =
                link.getAttribute("href");


            if (
                !targetId ||
                targetId === "#"
            ) {

                return;

            }


            const target =
                document.querySelector(targetId);


            if (!target) {
                return;
            }


            event.preventDefault();


            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });

    });


    /* =====================================================
       CARD KEYBOARD ACCESSIBILITY
       ===================================================== */

    const clickableCards =
        document.querySelectorAll(
            "[data-card-link]"
        );


    clickableCards.forEach(function (card) {

        card.setAttribute(
            "tabindex",
            "0"
        );


        card.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {

                    event.preventDefault();

                    card.click();

                }

            }
        );

    });


    /* =====================================================
       BACK TO TOP BUTTON
       Automatically creates button
       ===================================================== */

    const backToTop =
        document.createElement("button");


    backToTop.type = "button";

    backToTop.className =
        "roomfinder-back-to-top";

    backToTop.innerHTML =
        '<i class="bi bi-arrow-up"></i>';

    backToTop.setAttribute(
        "aria-label",
        "Back to top"
    );


    document.body.appendChild(
        backToTop
    );


    window.addEventListener(
        "scroll",
        function () {

            if (window.scrollY > 400) {

                backToTop.classList.add(
                    "show"
                );

            }

            else {

                backToTop.classList.remove(
                    "show"
                );

            }

        }
    );


    backToTop.addEventListener(
        "click",
        function () {

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });

        }
    );


    /* =====================================================
       GLOBAL MESSAGE FUNCTION
       ===================================================== */

    window.showRoomFinderMessage =
        showRoomFinderMessage;


    function showRoomFinderMessage(
        message,
        type = "info"
    ) {

        /*
         * Bootstrap alert container
         */

        let container =
            document.querySelector(
                ".roomfinder-message-container"
            );


        if (!container) {

            container =
                document.createElement("div");

            container.className =
                "roomfinder-message-container";

            document.body.appendChild(
                container
            );

        }


        const alert =
            document.createElement("div");


        alert.className =
            `alert alert-${type} alert-dismissible fade show roomfinder-message`;

        alert.setAttribute(
            "role",
            "alert"
        );


        alert.innerHTML = `

            <i class="bi bi-info-circle me-2"></i>

            <span>${escapeHTML(message)}</span>

            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="alert"
                aria-label="Close"
            ></button>

        `;


        container.appendChild(
            alert
        );


        /*
         * Automatically remove after 5 seconds.
         */

        setTimeout(function () {

            if (
                typeof bootstrap !== "undefined"
            ) {

                const instance =
                    bootstrap.Alert.getOrCreateInstance(
                        alert
                    );

                instance.close();

            }

            else {

                alert.remove();

            }

        }, 5000);

    }


    /* =====================================================
       SECURITY
       Escape text before putting it into HTML
       ===================================================== */

    function escapeHTML(value) {

        const div =
            document.createElement("div");

        div.textContent =
            String(value);

        return div.innerHTML;

    }


    /* =====================================================
       CURRENT YEAR
       Automatically updates footer year
       
       HTML:
       <span data-current-year></span>
       ===================================================== */

    const yearElements =
        document.querySelectorAll(
            "[data-current-year]"
        );


    yearElements.forEach(function (element) {

        element.textContent =
            new Date().getFullYear();

    });


});