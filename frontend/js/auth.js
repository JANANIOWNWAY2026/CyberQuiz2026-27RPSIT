
/* =========================================
   CYBERQUIZ - AUTHENTICATION JAVASCRIPT
   File: frontend/js/auth.js
========================================= */

"use strict";

// FastAPI backend address
const API_BASE_URL = "http://127.0.0.1:8000";

/*
 * Display a message inside the form.
 */
function showAuthMessage(form, message, isError = true) {
    let messageBox = form.querySelector(".auth-message");

    if (!messageBox) {
        messageBox = document.createElement("p");
        messageBox.className = "auth-message";
        messageBox.setAttribute("role", "status");
        messageBox.setAttribute("aria-live", "polite");
        form.prepend(messageBox);
    }

    messageBox.textContent = message;
    messageBox.style.color = isError ? "#ff6b81" : "#42f5c5";
}

/*
 * Send a request to the FastAPI backend.
 */
async function sendAuthRequest(endpoint, payload) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    let data = {};

    try {
        data = await response.json();
    } catch {
        // The server may return an empty or non-JSON response.
    }

    if (!response.ok) {
        throw new Error(
            data.detail || data.message || `Request failed (${response.status}).`
        );
    }

    return data;
}

/*
 * Participant registration
 */
function initializeRegistration() {
    const form = document.getElementById("registerForm");

    if (!form) {
        return;
    }

    form.addEventListener("submit", async event => {
        event.preventDefault();

        if (!form.reportValidity()) {
            return;
        }

        const formData = new FormData(form);
        const password = String(formData.get("password") || "");
        const confirmPassword = String(
            formData.get("confirmPassword") ||
            formData.get("confirm_password") ||
            ""
        );

        if (confirmPassword && password !== confirmPassword) {
            showAuthMessage(form, "Passwords do not match.");
            return;
        }

        const payload = {
            name: formData.get("name") || formData.get("full_name"),
            register_number:
                formData.get("register_number") ||
                formData.get("registerNumber"),
            gender: formData.get("gender"),
            phone:
                formData.get("phone") ||
                formData.get("contact_number"),
            email: formData.get("email"),
            college_name:
                formData.get("college_name") ||
                formData.get("college"),
            college_location: formData.get("college_location"),
            department: formData.get("department"),
            course: formData.get("course"),
            password: password
        };


        // Remove fields that are not present in the form.
        Object.keys(payload).forEach(key => {
            if (payload[key] === null || payload[key] === "") {
                delete payload[key];
            }
        });

        const submitButton = form.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

        if (submitButton) {
            submitButton.disabled = true;
        }

        try {
            const result = await sendAuthRequest(
                "/api/auth/register",
                payload
            );

            showAuthMessage(
                form,
                result.message ||
                "Registration submitted. Wait for admin approval.",
                false
            );

            form.reset();
        } catch (error) {
            showAuthMessage(
                form,
                error.message ||
                "Could not connect to the server. Please try again."
            );
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
            }
        }
    });
}

/*
 * Participant login
 */
function initializeParticipantLogin() {
    const form = document.getElementById("loginForm");

    if (!form) {
        return;
    }

    form.addEventListener("submit", async event => {
        event.preventDefault();

        if (!form.reportValidity()) {
            return;
        }

        const formData = new FormData(form);

        const payload = {
            email: formData.get("email"),
            password: formData.get("password")
        };
        const submitButton = form.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

        if (submitButton) {
            submitButton.disabled = true;
        }

        try {
            const result = await sendAuthRequest(
                "/api/auth/login",
                payload
            );

            if (result.access_token) {
                // Temporary development storage.
                // Production apps should prefer secure HttpOnly cookies.
                sessionStorage.setItem(
                    "cyberquiz_access_token",
                    result.access_token
                );
            }

            const isApproved = result.participant?.is_approved;

            if (isApproved !== true) {
                showAuthMessage(
                    form,
                    "Your account is waiting for admin approval."
                );
                return;
            }

            showAuthMessage(
                form,
                result.message ||
                "Login successful. Backend response received.",
                false
            );

            // Redirect only when the backend confirms approval.
            if (isApproved === true) {
                window.location.href = "waiting.html";
            }
        } catch (error) {
            showAuthMessage(
                form,
                error.message ||
                "Login failed. Check your details and try again."
            );
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
            }
        }
    });
}

/*
 * Show or hide password fields.
 */
function initializePasswordToggles() {
    document.querySelectorAll("[data-toggle-password]").forEach(button => {
        button.addEventListener("click", () => {
            const targetId = button.getAttribute("data-toggle-password");
            const input = document.getElementById(targetId);

            if (!input) {
                return;
            }

            const shouldShow = input.type === "password";
            input.type = shouldShow ? "text" : "password";

            button.setAttribute(
                "aria-label",
                shouldShow ? "Hide password" : "Show password"
            );
        });
    });
}

/*
 * Initialize forms when the page loads.
 */
document.addEventListener("DOMContentLoaded", () => {
    initializeRegistration();
    initializeParticipantLogin();
    initializePasswordToggles();
});