
/*
 * CyberQuiz Exam Guard
 * Detects when the quiz page becomes hidden.
 *
 * Requires the quiz page to provide:
 *   window.CyberQuizExamGuard.submit(reason)
 *
 * This file does not claim to block every way of leaving a browser.
 */

(function () {
    "use strict";

    let violationDetected = false;
    let submitInProgress = false;

    function reportMessage(message) {
        let box = document.getElementById("examGuardMessage");

        if (!box) {
            box = document.createElement("div");
            box.id = "examGuardMessage";
            box.setAttribute("role", "alert");

            Object.assign(box.style, {
                position: "fixed",
                left: "16px",
                right: "16px",
                bottom: "16px",
                zIndex: "99999",
                padding: "16px",
                background: "#40151b",
                color: "#ffffff",
                border: "1px solid #ff6b6b",
                borderRadius: "10px",
                fontFamily: "Arial, sans-serif"
            });

            document.body.appendChild(box);
        }

        box.textContent = message;
    }

    async function handleViolation(reason) {
        if (violationDetected || submitInProgress) {
            return;
        }

        violationDetected = true;
        submitInProgress = true;

        reportMessage(
            "Exam violation detected. Submitting your quiz..."
        );

        try {
            if (
                window.CyberQuizExamGuard &&
                typeof window.CyberQuizExamGuard.submit === "function"
            ) {
                await window.CyberQuizExamGuard.submit(reason);
            } else {
                reportMessage(
                    "Violation detected, but official submission is not configured."
                );

                submitInProgress = false;
            }
        } catch (error) {
            console.error("Exam guard submission failed:", error);

            reportMessage(
                "Submission could not be confirmed. Please contact the exam administrator."
            );

            submitInProgress = false;
        }
    }

    document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") {
            handleViolation("page_hidden");
        }
    });

    window.addEventListener("pagehide", function () {
        // This event may also occur during normal navigation.
        // Do not rely on it as proof of cheating.
    });

    window.CyberQuizExamGuard = {
        submit: null,

        isViolationDetected: function () {
            return violationDetected;
        }
    };
})();
