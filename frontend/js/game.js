
/* =========================================
   CYBERQUIZ - QUIZ GAME JAVASCRIPT
   File: frontend/js/game.js
========================================= */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const questionText = document.getElementById("questionText");
    const optionsContainer = document.getElementById("optionsContainer");
    const nextButton = document.getElementById("nextButton");
    const previousButton = document.getElementById("previousButton");
    const timerElement = document.getElementById("timer");
    const progressElement = document.getElementById("progressText");
    const progressBar = document.getElementById("progressBar");
    const levelElement = document.getElementById("levelText");

    if (
        !questionText ||
        !optionsContainer ||
        !nextButton ||
        !previousButton ||
        !timerElement
    ) {
        console.error("Quiz HTML elements are missing. Check game.html IDs.");
        return;
    }

    const LEVELS = {
    1: { questionCount: 15, secondsPerQuestion: 50 },
    2: { questionCount: 10, secondsPerQuestion: 40 },
    3: { questionCount: 10, secondsPerQuestion: 30 }
};

    // Read the level from the URL.
    const requestedLevel = Number(
        new URLSearchParams(window.location.search).get("level") || 1
    );

    let currentLevel = LEVELS[requestedLevel] ? requestedLevel : 1;
    let currentQuestionIndex = 0;
    let secondsRemaining = LEVELS[currentLevel].secondsPerQuestion;
    let timerInterval = null;
    let selectedAnswer = null;
    let answers = [];
    let isSubmitting = false;
   const API_BASE = "https://cyberquiz-backend.onrender.com";
const token = sessionStorage.getItem("cyberquiz_access_token");

let sessionId = null;
let backendQuestions = [];
let deadlineAt = null;

    /*
     * Scenario-based cybersecurity questions.
     * Original question text and options are preserved.
     */
    let questionBank = [
        {
            question: "An employee receives an email that appears to come from the IT team. It asks them to sign in through a shortened URL to prevent account suspension. What is the safest first action?",
            options: [
                "Open the URL in incognito mode",
                "Verify the request through an independently known IT contact",
                "Reply to the email and ask if it is genuine",
                "Open the URL but do not download anything"
            ]
        },
        {
            question: "A user enters their password on a fake login page but notices the mistake immediately. What should they do first?",
            options: [
                "Delete browser history and continue working",
                "Wait to see whether suspicious activity occurs",
                "Change the password using the legitimate site and report the incident",
                "Change only the email display name"
            ]
        },
        {
            question: "A server receives thousands of requests from many compromised devices, making its service unavailable. Which attack best matches this behaviour?",
            options: [
                "Distributed denial-of-service attack",
                "SQL injection",
                "Privilege escalation",
                "Directory traversal"
            ]
        },
        {
            question: "A web application places user input directly into an SQL query. An attacker changes the input so the database executes unintended query logic. Which weakness is being exploited?",
            options: [
                "Cross-site request forgery",
                "SQL injection",
                "DNS poisoning",
                "Insecure file permissions only"
            ]
        },
        {
            question: "A staff member receives an unexpected attachment claiming to be an urgent invoice. Which response best reduces the risk?",
            options: [
                "Enable macros so the invoice displays correctly",
                "Forward the attachment to colleagues for testing",
                "Verify the sender and inspect it through approved security procedures",
                "Rename the file extension before opening it"
            ]
        },
        {
            question: "An attacker steals a session cookie from a logged-in user and reuses it to access the account. What is the attack called?",
            options: [
                "Session hijacking",
                "Port scanning",
                "Password spraying",
                "Data masking"
            ]
        },
        {
            question: "A company uses MFA, but an employee approves an unexpected sign-in prompt after receiving repeated prompts. What attack technique may be involved?",
            options: [
                "MFA fatigue or push bombing",
                "ARP table hardening",
                "Certificate pinning",
                "Secure boot"
            ]
        },
        {
            question: "A web server's logs show repeated attempts to access files using paths containing ../ sequences. What should the security team investigate?",
            options: [
                "Directory or path traversal attempts",
                "A normal TLS handshake",
                "A successful software update",
                "A routine DHCP lease renewal"
            ]
        },
        {
            question: "A developer stores API credentials directly in a public Git repository. What is the most appropriate response?",
            options: [
                "Rename the repository and keep the credentials",
                "Revoke or rotate exposed credentials and remove the exposure",
                "Delete only the latest commit and assume the secret is safe",
                "Make the secret harder to read using uppercase letters"
            ]
        },
        {
            question: "A workstation begins encrypting files and displays a ransom demand. What should the responder generally do first?",
            options: [
                "Pay immediately without investigating",
                "Disconnect or isolate the affected system according to incident procedures",
                "Delete all logs to stop disk usage",
                "Connect backup drives to check whether they work"
            ]
        },
        {
            question: "A user has read access to payroll records but discovers they can also modify salaries due to excessive permissions. Which security principle was most directly violated?",
            options: [
                "Least privilege",
                "Availability",
                "Security through obscurity",
                "Data compression"
            ]
        },
        {
            question: "A public Wi-Fi network uses a look-alike name similar to a nearby cafe. An attacker controls that network. What is this commonly called?",
            options: [
                "Evil twin access point",
                "Blue-green deployment",
                "Cold boot prevention",
                "Database sharding"
            ]
        },
        {
            question: "An application displays detailed database error messages, including table names and query details, to unauthenticated users. What is the primary concern?",
            options: [
                "Information disclosure that may help further attacks",
                "Improved encryption strength",
                "Automatic privilege reduction",
                "Guaranteed protection against injection"
            ]
        },
        {
            question: "An attacker tries a small list of commonly used passwords against many different employee accounts. Which technique does this describe?",
            options: [
                "Password spraying",
                "Credential hashing",
                "File carving",
                "Network segmentation"
            ]
        },
        {
            question: "A security analyst finds a login from an unfamiliar country shortly after a successful login from the employee's usual location. What is the best next step?",
            options: [
                "Assume the employee is travelling and close the alert",
                "Investigate identity, session, device and authentication evidence",
                "Delete the unfamiliar login record",
                "Disable all company accounts permanently"
            ]
        },
        {
            question: "A website accepts uploaded files and stores them in a directory where the web server can execute scripts. What is the strongest relevant mitigation?",
            options: [
                "Trust the file extension supplied by the browser",
                "Store uploads outside executable web paths and validate them securely",
                "Allow all file types but rename them",
                "Hide the upload button with CSS"
            ]
        },
        {
            question: "An attacker intercepts network traffic and secretly alters communications between two parties. Which attack best describes this?",
            options: [
                "Man-in-the-middle attack",
                "Brute-force hashing",
                "Secure deletion",
                "Load balancing"
            ]
        },
        {
            question: "A company wants to reduce the impact of one compromised workstation spreading to critical servers. Which control is most relevant?",
            options: [
                "Network segmentation and restricted access",
                "Using the same local administrator password everywhere",
                "Disabling security logging",
                "Allowing unrestricted east-west traffic"
            ]
        },
        {
            question: "An attacker changes a user's account role by modifying a role value sent in a request. The server trusts that value without checking authorization. What is the core flaw?",
            options: [
                "Broken access control",
                "Excessive password entropy",
                "Strong certificate validation",
                "Encrypted database backups"
            ]
        },
        {
            question: "A system's SHA-256 password hashes are stolen. Which password-storage approach best improves resistance to offline guessing?",
            options: [
                "Store passwords using reversible encryption only",
                "Use a unique salt with a purpose-built password hashing algorithm such as Argon2id",
                "Use the same unsalted hash for every user",
                "Convert passwords to Base64 before storing them"
            ]
        },
        {
            question: "A DNS response redirects users from a legitimate domain to an attacker's server. Which area should investigators examine?",
            options: [
                "DNS resolution integrity and related records",
                "Monitor refresh rate",
                "Keyboard driver versions only",
                "Printer spooler size only"
            ]
        },
        {
            question: "A developer checks authorization only in the browser interface. An attacker calls the protected API directly and retrieves another user's records. What failed?",
            options: [
                "Server-side authorization enforcement",
                "CSS encapsulation",
                "Client-side image compression",
                "DNS caching"
            ]
        },
        {
            question: "A security team discovers a known vulnerability on an internet-facing server. A patch is available, but immediate patching requires testing. What is the best risk-based response?",
            options: [
                "Ignore it until the next annual review",
                "Assess exposure, apply suitable mitigations, test and deploy the patch promptly",
                "Disable monitoring while deciding",
                "Publish the server's credentials so users can report issues"
            ]
        },
        {
            question: "An attacker compromises a legitimate employee account and uses it to access cloud resources. Which evidence is especially useful for detecting suspicious use?",
            options: [
                "Identity sign-in logs, device context and cloud audit events",
                "Desktop wallpaper settings only",
                "The employee's monitor resolution",
                "The number of keyboard shortcuts used"
            ]
        },
        {
            question: "A website reflects untrusted input into a page, and the browser executes it as JavaScript. Which vulnerability is most likely?",
            options: [
                "Cross-site scripting",
                "Distributed denial of service",
                "Disk encryption",
                "Secure password hashing"
            ]
        },
        {
            question: "A company receives a message that appears to come from its CEO, urgently requesting a bank transfer and secrecy. What should the finance employee do?",
            options: [
                "Transfer the money because the sender is senior",
                "Verify the request using an independent trusted communication channel",
                "Reply to the same message asking for a confirmation emoji",
                "Share the banking password to validate the request"
            ]
        },
        {
            question: "A backup system is always writable using the same administrator credentials as production servers. Which improvement best limits ransomware impact?",
            options: [
                "Use isolated or immutable backups and separate access controls",
                "Give every workstation write access to backups",
                "Disable backup verification",
                "Keep only one permanently connected backup copy"
            ]
        },
        {
            question: "A process unexpectedly launches a command shell and contacts a newly registered external domain. What should an analyst do?",
            options: [
                "Investigate process lineage, network activity and endpoint telemetry",
                "Assume every shell process is malicious and erase the disk",
                "Ignore the event if the user is an administrator",
                "Delete event logs before collecting evidence"
            ]
        },
        {
            question: "A company needs to prove that a file has not changed since evidence collection. Which practice best supports integrity verification?",
            options: [
                "Calculate and record a cryptographic hash and maintain chain of custody",
                "Rename the file several times",
                "Email it through multiple personal accounts",
                "Change its permissions without recording the action"
            ]
        },
        {
            question: "A cloud storage bucket containing customer records is accidentally configured for public access. What should the team prioritize?",
            options: [
                "Restrict public access, assess exposure and investigate access logs",
                "Change the bucket display name only",
                "Delete the audit history",
                "Assume encryption alone makes public access harmless"
            ]
        },
        {
            question: "An endpoint detection alert identifies suspicious credential dumping on a workstation. What is a sensible incident response action?",
            options: [
                "Contain the endpoint, preserve evidence and investigate credential exposure",
                "Ask the user to keep working without reporting it",
                "Disable all security controls to avoid false positives",
                "Delete the alert before collecting telemetry"
            ]
        },
        {
            question: "A TLS certificate warning appears on a sensitive login page. What is the safest response?",
            options: [
                "Continue and enter credentials because HTTPS is shown",
                "Stop and verify the site's identity and certificate issue",
                "Disable certificate checks permanently",
                "Share the warning screenshot with the password included"
            ]
        },
        {
            question: "A service account has domain-wide administrator privileges even though it only needs to read one application database. What should be changed?",
            options: [
                "Reduce its privileges to the minimum required and review its credentials",
                "Keep the privileges to avoid configuration work",
                "Share its secret with developers",
                "Disable account monitoring"
            ]
        },
        {
            question: "An analyst sees repeated failed logins followed by one successful login from the same source. Which interpretation is most appropriate?",
            options: [
                "It may indicate password guessing followed by a successful compromise and needs investigation",
                "It proves the account is safe because one login succeeded",
                "It always indicates a normal software update",
                "It confirms a denial-of-service attack without further evidence"
            ]
        },
        {
            question: "During an incident, a team needs to restore services while preserving evidence. Which approach is most appropriate?",
            options: [
                "Follow the incident response plan, preserve relevant evidence and restore from verified clean systems",
                "Wipe every system immediately without recording anything",
                "Reconnect affected machines before checking them",
                "Disable backups and discard system logs"
            ]
        }
    ];

    function getQuestionForCurrentIndex() {
    return questionBank[currentQuestionIndex];
}

    
function renderQuestion() {
    const question = getQuestionForCurrentIndex();

    selectedAnswer =
        answers[currentQuestionIndex]?.selectedOption ?? null;

    questionText.textContent = question.question;
    optionsContainer.replaceChildren();

    question.options.forEach((option, index) => {
        const label = document.createElement("label");
        label.className = "quiz-option";

        const radio = document.createElement("input");
        radio.type = "radio";
        radio.name = "quizAnswer";
        radio.value = String(index);
        radio.checked = selectedAnswer === index;

        const optionText = document.createElement("span");
        optionText.textContent =
            `${String.fromCharCode(65 + index)}. ${option}`;

        if (radio.checked) {
            label.classList.add("selected");
        }

        radio.addEventListener("change", () => {
            selectedAnswer = index;

            // Save the selected answer in the local answer array.
            answers[currentQuestionIndex] = {
                ...answers[currentQuestionIndex],
                selectedOption: index,
                timedOut: false
            };

            optionsContainer
                .querySelectorAll(".quiz-option")
                .forEach(item => item.classList.remove("selected"));

            label.classList.add("selected");
        });

        label.append(radio, optionText);
        optionsContainer.appendChild(label);
    });

    updateProgress();
    startTimer();
}

    function updateProgress() {
        const total = LEVELS[currentLevel].questionCount;
        const current = currentQuestionIndex + 1;

        if (progressElement) {
            progressElement.textContent =
                `Question ${current} of ${total}`;
        }

        if (progressBar) {
            progressBar.style.width = `${(current / total) * 100}%`;
        }

        if (levelElement) {
            levelElement.textContent = `Level ${currentLevel}`;
        }

        nextButton.textContent =
            currentQuestionIndex === total - 1
                ? "Submit Level"
                : "Save & Next";

        previousButton.disabled = true;
        previousButton.hidden = true;
    }


function startTimer() {
    clearInterval(timerInterval);

    secondsRemaining = LEVELS[currentLevel].secondsPerQuestion;
    updateTimerDisplay();

    timerInterval = setInterval(() => {
        secondsRemaining -= 1;
        updateTimerDisplay();

        if (secondsRemaining <= 0) {
            clearInterval(timerInterval);
            timerInterval = null;

            saveAnswerAndContinue(true);
        }
    }, 1000);
}

    function updateTimerDisplay() {
        const minutes = Math.floor(secondsRemaining / 60);
        const seconds = secondsRemaining % 60;

        timerElement.textContent =
            `${String(minutes).padStart(2, "0")}:` +
            `${String(seconds).padStart(2, "0")}`;

        timerElement.classList.toggle(
            "timer-warning",
            secondsRemaining <= 5
        );
    }

    function saveCurrentAnswer(isTimeout = false) {
        answers[currentQuestionIndex] = {
            questionIndex: currentQuestionIndex,
            selectedOption: selectedAnswer,
            timedOut: isTimeout
        };
    }

    function saveAnswerAndContinue(isTimeout = false) {
        if (isSubmitting) {
            return;
        }

        clearInterval(timerInterval);
        saveCurrentAnswer(isTimeout);

        const total = LEVELS[currentLevel].questionCount;

        if (currentQuestionIndex < total - 1) {
            currentQuestionIndex += 1;
            renderQuestion();
            return;
        }

        finishLevel();
    }

    function goToPreviousQuestion() {
        // Going back to previous questions is not allowed.
        return;
    }

    async function finishLevel() {
    if (isSubmitting) return;

    isSubmitting = true;
    clearInterval(timerInterval);

    nextButton.disabled = true;
    previousButton.hidden = true;

    try {
        const submittedAnswers = {};

        answers.forEach((answer, index) => {
            if (
                answer &&
                answer.selectedOption !== null &&
                backendQuestions[index]
            ) {
                const questionId = backendQuestions[index].id;
                const selectedLetter =
                    String.fromCharCode(65 + answer.selectedOption);

                submittedAnswers[questionId] = selectedLetter;
            }
        });

        const response = await fetch(
            `${API_BASE}/api/quiz/submit`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    answers: submittedAnswers
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Quiz submission failed"
            );
        }

        sessionStorage.setItem(
            `cyberquiz_level_${currentLevel}_submitted`,
            "true"
        );

        // After submission, wait for the administrator.
        window.location.replace("waiting.html");

    } catch (error) {
        console.error("Quiz submission failed:", error);

        isSubmitting = false;
        nextButton.disabled = false;

        alert(
            "Quiz submit aagala paa. Internet/backend check pannitu retry pannunga."
        );
    }
}


async function initializeQuiz() {
    if (!token) {
        window.location.replace("login.html");
        return;
    }

    try {
        const startResponse = await fetch(
            `${API_BASE}/api/quiz/start/${currentLevel}`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Accept": "application/json"
                }
            }
        );

        const startData = await startResponse.json();

        if (!startResponse.ok) {
            throw new Error(
                startData.detail || "Unable to start quiz"
            );
        }

        sessionId = startData.session_id;
        deadlineAt = startData.deadline_at;

        const questionsResponse = await fetch(
            `${API_BASE}/api/quiz/questions/${currentLevel}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Accept": "application/json"
                }
            }
        );

        const questionsData = await questionsResponse.json();

        if (!questionsResponse.ok) {
            throw new Error(
                questionsData.detail || "Unable to load questions"
            );
        }

        backendQuestions = questionsData;

        questionBank = questionsData.map(question => ({
            id: question.id,
            question: question.question_text,
            options: [
                question.options.A,
                question.options.B,
                question.options.C,
                question.options.D
            ]
        }));

        const expectedCount = LEVELS[currentLevel].questionCount;

        if (questionBank.length !== expectedCount) {
            throw new Error(
                `Level ${currentLevel} needs ${expectedCount} questions, but backend returned ${questionBank.length}.`
            );
        }

        const savedAnswers = startData.answers || {};

        answers = questionBank.map(question => {
            const selected = savedAnswers[question.id];

            return {
                selectedOption: selected
                    ? ["A", "B", "C", "D"].indexOf(selected)
                    : null,
                timedOut: false
            };
        });

        currentQuestionIndex = Number(
            startData.current_question_index ?? 0
        );

        if (
            currentQuestionIndex < 0 ||
            currentQuestionIndex >= questionBank.length
        ) {
            currentQuestionIndex = 0;
        }

        renderQuestion();

   
    } catch (error) {
        console.error("Quiz initialization failed:", error);

        questionText.textContent = "Unable to start the quiz.";
        optionsContainer.replaceChildren();
        nextButton.disabled = true;
        timerElement.textContent = "--:--";

        alert(
            `${error.message}\n\nPlease check whether the backend is running, the participant is approved, and the round is active and unlocked.`
        );
    }
}

nextButton.addEventListener("click", event => {
    event.preventDefault();
    saveAnswerAndContinue(false);
});

previousButton.addEventListener("click", event => {
    event.preventDefault();
    goToPreviousQuestion();
});

// Prevent duplicate timer activity when leaving the page.
window.addEventListener("pagehide", () => {
    clearInterval(timerInterval);
});
// Connect Exam Guard to the existing quiz submission function.
if (window.CyberQuizExamGuard) {
    window.CyberQuizExamGuard.submit = async function (reason) {
        console.warn("Exam Guard triggered:", reason);

        // Save the answer selected for the current question.
        saveCurrentAnswer(false);

        // Reuse the existing backend submission logic.
        await finishLevel();
    };
}

initializeQuiz();
});

