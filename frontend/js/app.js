
/* =========================================
   CYBERQUIZ - MAIN FRONTEND JAVASCRIPT
   File: frontend/js/app.js
   ========================================= */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    initializeMobileMenu();
    updateFooterYear();
    initializeSmoothNavigation();
});

/*
 * Mobile navigation menu
 */
function initializeMobileMenu() {
    const menuToggle = document.getElementById("menuToggle");
    const navLinks = document.querySelector(".nav-links");

    if (!menuToggle || !navLinks) {
        return;
    }

    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open navigation menu");

    menuToggle.addEventListener("click", () => {
        const isOpen = navLinks.classList.toggle("open");

        menuToggle.setAttribute("aria-expanded", String(isOpen));
        menuToggle.setAttribute(
            "aria-label",
            isOpen ? "Close navigation menu" : "Open navigation menu"
        );
    });

    navLinks.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            navLinks.classList.remove("open");
            menuToggle.setAttribute("aria-expanded", "false");
            menuToggle.setAttribute("aria-label", "Open navigation menu");
        });
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            navLinks.classList.remove("open");
            menuToggle.setAttribute("aria-expanded", "false");
            menuToggle.setAttribute("aria-label", "Open navigation menu");
        }
    });
}

/*
 * Automatically display the current year in the footer
 */
function updateFooterYear() {
    document.querySelectorAll("#currentYear, [data-current-year]")
        .forEach(element => {
            element.textContent = String(new Date().getFullYear());
        });
}

/*
 * Smooth scrolling for in-page navigation links
 */
function initializeSmoothNavigation() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener("click", event => {
            const targetId = link.getAttribute("href");

            if (!targetId || targetId === "#") {
                return;
            }

            const target = document.getElementById(targetId.slice(1));

            if (!target) {
                return;
            }

            event.preventDefault();

            target.scrollIntoView({
                behavior: window.matchMedia(
                    "(prefers-reduced-motion: reduce)"
                ).matches ? "auto" : "smooth",
                block: "start"
            });
        });
    });
}