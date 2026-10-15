
/* =========================================
   CYBERQUIZ - ADMIN DASHBOARD JAVASCRIPT
   File: frontend/js/admin.js
========================================= */

"use strict";

const ADMIN_API_BASE_URL = "http://127.0.0.1:8000";

let allAdminParticipants = [];
let allAdminResults = [];

async function adminApiRequest(endpoint, options = {}) {
    const token = localStorage.getItem("cyberquiz_admin_token");

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${ADMIN_API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    let data = {};

    try {
        data = await response.json();
    } catch {
        // The server may return an empty response.
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            `Request failed (${response.status}).`
        );
    }

    return data;
}

function showAdminMessage(message, isError = false) {
    let status = document.getElementById("adminStatusMessage");

    if (!status) {
        status = document.createElement("p");
        status.id = "adminStatusMessage";
        status.setAttribute("role", "status");
        status.setAttribute("aria-live", "polite");

        (document.querySelector("main") || document.body)
            .prepend(status);
    }

    status.textContent = message;
    status.style.color = isError ? "#ff6b81" : "#42f5c5";
}

function createCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = String(value ?? "—");
    row.appendChild(cell);
    return cell;
}

function getParticipantId(participant) {
    return participant.id ?? participant.user_id;
}

function getRoundApprovals(participant) {
    return participant.round_approvals || {
        "1": false,
        "2": false,
        "3": false
    };
}

/* =========================================
   PARTICIPANTS AND APPROVALS
========================================= */

async function loadAdminParticipants() {
    const tableBody = document.querySelector(
        "#participantsTable tbody, #participantTableBody, #participantTable"
    );

    if (!tableBody) return;

    try {
        const result = await adminApiRequest("/api/admin/participants");

        allAdminParticipants = Array.isArray(result)
            ? result
            : result.participants || [];

        updateParticipantMetrics();
        renderAdminParticipants();
    } catch (error) {
        showAdminMessage(
            `Could not load participants: ${error.message}`,
            true
        );
    }
}

function updateParticipantMetrics() {
    const registeredCount = document.getElementById("registeredCount");
    const pendingCount = document.getElementById("pendingCount");

    if (registeredCount) {
        registeredCount.textContent = allAdminParticipants.length;
    }

    if (pendingCount) {
        pendingCount.textContent = allAdminParticipants.filter(
            participant => !participant.is_approved
        ).length;
    }
}

function renderAdminParticipants() {
    const tableBody = document.querySelector(
        "#participantsTable tbody, #participantTableBody, #participantTable"
    );

    if (!tableBody) return;

    const searchInput = document.getElementById("participantSearch");
    const approvalFilter = document.getElementById("approvalFilter");

    const searchTerm = (searchInput?.value || "").trim().toLowerCase();
    const filter = approvalFilter?.value || "all";

    const participants = allAdminParticipants.filter(participant => {
        const searchable = [
            participant.name,
            participant.full_name,
            participant.register_number,
            participant.email,
            participant.college_name,
            participant.department
        ].filter(Boolean).join(" ").toLowerCase();

        if (searchTerm && !searchable.includes(searchTerm)) {
            return false;
        }

        if (filter === "pending" && participant.is_approved) {
            return false;
        }

        if (filter === "approved" && !participant.is_approved) {
            return false;
        }

        if (filter === "rejected" && participant.is_active !== false) {
            return false;
        }

        return true;
    });

    tableBody.replaceChildren();

    if (!participants.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 11;
        cell.textContent = "No participants found.";
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    participants.forEach(participant => {
        const row = document.createElement("tr");
        const participantId = getParticipantId(participant);


        createCell(row, participant.name || participant.full_name || "—");
        createCell(row, participant.register_number);
        createCell(row, participant.email);
        createCell(row, participant.phone);
        createCell(row, participant.college_name);
       createCell(row, participant.department);

const approvals = getRoundApprovals(participant);

[1, 2, 3].forEach(level => {
    const isApproved = approvals[String(level)];

    const badge = document.createElement("span");
    badge.textContent = isApproved ? "Approved" : "Pending";
    badge.className = isApproved
        ? "approval-status approved"
        : "approval-status pending";

    const cell = document.createElement("td");
    cell.appendChild(badge);
    row.appendChild(cell);
});
       



        // Global account approval
        const statusCell = document.createElement("td");
        const statusBadge = document.createElement("span");

        statusBadge.textContent = participant.is_approved
            ? "Account Approved"
            : "Account Pending";

        statusBadge.className = participant.is_approved
            ? "approval-status approved"
            : "approval-status pending";

        statusCell.appendChild(statusBadge);
        row.appendChild(statusCell);

        // Individual level approval controls
        const actionCell = document.createElement("td");
        actionCell.style.minWidth = "230px";

        if (!participant.is_approved) {
            const accountButton = document.createElement("button");
            accountButton.type = "button";
            accountButton.textContent = "Approve Account";

            accountButton.addEventListener("click", async () => {
                accountButton.disabled = true;

                try {
                    await approveParticipant(participantId);
                } finally {
                    accountButton.disabled = false;
                }
            });

            actionCell.appendChild(accountButton);
        }

        const approvalLabel = document.createElement("p");
        approvalLabel.textContent = "Round approvals:";
        actionCell.appendChild(approvalLabel);

        

        [1, 2, 3].forEach(level => {
            const isApproved = getRoundApprovals(participant)[String(level)];
            const line = document.createElement("div");
            line.style.marginBottom = "6px";

            const badge = document.createElement("span");
            badge.textContent = `L${level}: ${approvals[String(level)] ? "Approved" : "Pending"
                }`;
            badge.style.marginRight = "8px";

            const button = document.createElement("button");
            button.type = "button";
            button.textContent = approvals[String(level)]
                ? "Revoke"
                : `Approve L${level}`;

            button.addEventListener("click", async () => {
                button.disabled = true;

                try {
                    await setParticipantRoundApproval(
                        participantId,
                        level,
                        !approvals[String(level)]
                    );
                } finally {
                    button.disabled = false;
                }
            });

            line.append(badge, button);
            actionCell.appendChild(line);
        });

        row.appendChild(actionCell);
        tableBody.appendChild(row);
    });
}

async function approveParticipant(participantId) {
    if (!participantId) {
        showAdminMessage("Participant ID is missing.", true);
        return;
    }

    try {
        await adminApiRequest(
            `/api/admin/participants/${encodeURIComponent(participantId)}/approve`,
            { method: "PATCH" }
        );

        showAdminMessage("Participant account approved.");
        await loadAdminParticipants();
    } catch (error) {
        showAdminMessage(`Account approval failed: ${error.message}`, true);
    }
}

async function setParticipantRoundApproval(
    participantId,
    level,
    isApproved
) {
    if (!participantId || ![1, 2, 3].includes(Number(level))) {
        showAdminMessage("Invalid participant or level.", true);
        return;
    }

    try {
        const result = await adminApiRequest(
            `/api/admin/participants/${encodeURIComponent(participantId)}/round-approval/${level}`,
            {
                method: "PATCH",
                body: JSON.stringify({ is_approved: isApproved })
            }
        );

        showAdminMessage(result.message || `Level ${level} approval updated.`);
        await loadAdminParticipants();
    } catch (error) {
        showAdminMessage(
            `Level ${level} approval failed: ${error.message}`,
            true
        );
    }
}

/* =========================================
   ROUND START / END / STATUS
========================================= */

async function startQuizRound(level) {
    level = Number(level);

    if (![1, 2, 3].includes(level)) {
        showAdminMessage("Choose a valid level.", true);
        return;
    }

    if (!window.confirm(
        `Start Level ${level}? Only participants approved for this level can begin.`
    )) {
        return;
    }

    try {
        const result = await adminApiRequest(
            `/api/admin/rounds/${level}/start`,
            { method: "PATCH", body: JSON.stringify({}) }
        );

        showAdminMessage(result.message || `Level ${level} started.`);
        await loadAdminRoundStatuses();
    } catch (error) {
        showAdminMessage(`Could not start Level ${level}: ${error.message}`, true);
    }
}

async function endQuizRound(level) {
    level = Number(level);

    if (![1, 2, 3].includes(level)) {
        showAdminMessage("Choose a valid level.", true);
        return;
    }

    if (!window.confirm(
        `End Level ${level}? New quiz sessions will be blocked. Existing sessions can continue until their deadlines.`
    )) {
        return;
    }

    try {
        const result = await adminApiRequest(
            `/api/admin/rounds/${level}/end`,
            { method: "PATCH", body: JSON.stringify({}) }
        );

        showAdminMessage(result.message || `Level ${level} ended.`);
        await loadAdminRoundStatuses();
    } catch (error) {
        showAdminMessage(`Could not end Level ${level}: ${error.message}`, true);
    }
}

// Compatibility with existing HTML buttons.
async function unlockQuizLevel(level) {
    await startQuizRound(level);
}

async function loadAdminRoundStatuses() {
    try {
        const rounds = await adminApiRequest("/api/admin/rounds/status");

        rounds.forEach(round => {
            const level = Number(round.level);
            const status = String(round.status || "locked").toLowerCase();

            const statusElement = document.querySelector(
                `[data-round-status="${level}"]`
            );

            if (statusElement) {
                statusElement.textContent = status.toUpperCase();
            }

            const startButton = document.querySelector(
                `[data-start-level="${level}"]`
            );

            const endButton = document.querySelector(
                `[data-end-level="${level}"]`
            );

            if (startButton) {
                startButton.disabled = status === "active";
                startButton.textContent = status === "active"
                    ? `Level ${level} Active`
                    : `Start Level ${level}`;
            }

            if (endButton) {
                endButton.disabled = status !== "active";
            }

            // Support the existing Unlock Level buttons.
            const unlockButton = document.querySelector(
                `[data-unlock-level="${level}"]`
            );

            if (unlockButton) {
                unlockButton.disabled = status === "active";
                unlockButton.textContent = status === "active"
                    ? `Level ${level} Active`
                    : `Start Level ${level}`;
            }

            if (level === 1) {
                const activeRound = document.getElementById("activeRound");
                if (activeRound) {
                    activeRound.textContent = status.toUpperCase();
                }
            }
        });
    } catch (error) {
        showAdminMessage(
            `Could not load round statuses: ${error.message}`,
            true
        );
    }
}

/* =========================================
   RESULTS
========================================= */


async function loadAdminResults() {
    const tableBody = document.querySelector(
        "#resultsTable tbody, #resultsTableBody"
    );

    if (!tableBody) return;

    try {
        const result = await adminApiRequest("/api/admin/results");

        allAdminResults = Array.isArray(result)
            ? result
            : result.results || [];

        tableBody.replaceChildren();

        const completedCount = document.getElementById("completedCount");

        if (completedCount) {
            completedCount.textContent = allAdminResults.filter(
                item => item.status === "Completed"
            ).length;
        }

        if (!allAdminResults.length) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 7;
            cell.textContent = "No participant results available yet.";
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        allAdminResults.forEach(item => {
            const row = document.createElement("tr");

            [
                item.participant_name || "—",
                item.total_questions ?? 0,
                item.correct_answers ?? 0,
                item.wrong_answers ?? 0,
                item.unanswered ?? 0,
                item.score ?? 0,
                item.status || "In Progress"
            ].forEach(value => createCell(row, value));

            tableBody.appendChild(row);
        });
    } catch (error) {
        showAdminMessage(
            `Could not load results: ${error.message}`,
            true
        );
    }
}

/* =========================================
   LEADERBOARD
========================================= */

async function loadLeaderboardStatus() {
    const status = document.getElementById("leaderboardPublishStatus");
    const publishButton = document.getElementById("publishLeaderboardButton");
    const hideButton = document.getElementById("hideLeaderboardButton");

    if (!status || !publishButton || !hideButton) return;

    try {
        const result = await adminApiRequest(
            "/api/admin/leaderboard-status"
        );

        if (result.is_published) {
            status.textContent = "Final results are PUBLISHED.";
            publishButton.disabled = true;
            hideButton.disabled = false;
        } else {
            status.textContent = "Final results are HIDDEN.";
            publishButton.disabled = false;
            hideButton.disabled = true;
        }
    } catch (error) {
        status.textContent = `Could not load publication status: ${error.message}`;
    }
}

async function setLeaderboardPublished(publish) {
    const action = publish ? "publish" : "unpublish";

    const message = publish
        ? "Publish the final leaderboard for all eligible participants?"
        : "Hide the final leaderboard from public view?";

    if (!window.confirm(message)) return;

    const publishButton = document.getElementById("publishLeaderboardButton");
    const hideButton = document.getElementById("hideLeaderboardButton");

    if (publishButton) publishButton.disabled = true;
    if (hideButton) hideButton.disabled = true;

    try {
        const result = await adminApiRequest(
            `/api/admin/leaderboard/${action}`,
            { method: "PATCH" }
        );

        showAdminMessage(result.message || "Leaderboard status updated.");
    } catch (error) {
        showAdminMessage(`Could not update leaderboard: ${error.message}`, true);
    } finally {
        await loadLeaderboardStatus();
    }
}

/* =========================================
   INITIALIZATION
========================================= */

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-approve-participant]").forEach(button => {
        button.addEventListener("click", () => {
            approveParticipant(
                button.getAttribute("data-approve-participant")
            );
        });
    });

    document.querySelectorAll("[data-unlock-level]").forEach(button => {
        button.addEventListener("click", () => {
            unlockQuizLevel(button.getAttribute("data-unlock-level"));
        });
    });

    document.querySelectorAll("[data-start-level]").forEach(button => {
        button.addEventListener("click", () => {
            startQuizRound(button.getAttribute("data-start-level"));
        });
    });

    document.querySelectorAll("[data-end-level]").forEach(button => {
        button.addEventListener("click", () => {
            endQuizRound(button.getAttribute("data-end-level"));
        });
    });

    const publishButton = document.getElementById("publishLeaderboardButton");
    if (publishButton) {
        publishButton.addEventListener("click", () => {
            setLeaderboardPublished(true);
        });
    }

    const hideButton = document.getElementById("hideLeaderboardButton");
    if (hideButton) {
        hideButton.addEventListener("click", () => {
            setLeaderboardPublished(false);
        });
    }

    const searchInput = document.getElementById("participantSearch");
    if (searchInput) {
        searchInput.addEventListener("input", renderAdminParticipants);
    }

    const approvalFilter = document.getElementById("approvalFilter");
    if (approvalFilter) {
        approvalFilter.addEventListener("change", renderAdminParticipants);
    }
    const authStatus = document.getElementById("adminAuthStatus");
    const token = localStorage.getItem("cyberquiz_admin_token");

    if (authStatus) {
        if (!token) {
            authStatus.textContent = "NOT AUTHENTICATED";
            authStatus.style.color = "#ffb4b4";
        } else {
            authStatus.textContent = "VERIFYING ADMIN ACCESS...";

            adminApiRequest("/api/admin/leaderboard-status")
                .then(() => {
                    authStatus.textContent = "ADMIN AUTHENTICATED";
                    authStatus.style.color = "#8cf5c3";
                })
                .catch(() => {
                    authStatus.textContent = "AUTHENTICATION FAILED";
                    authStatus.style.color = "#ffb4b4";
                });
        }
    }

    const refreshButton = document.getElementById("refreshAdminData");

    if (refreshButton) {
        refreshButton.addEventListener("click", async () => {
            await Promise.all([
                loadAdminParticipants(),
                loadAdminResults(),
                loadAdminRoundStatuses(),
                loadLeaderboardStatus()
            ]);
        });
    }

    async function initializeAdminDashboard() {
        const authStatus = document.getElementById("adminAuthStatus");
        const token = localStorage.getItem("cyberquiz_admin_token");

        if (!token) {
            if (authStatus) {
                authStatus.textContent = "LOGIN REQUIRED";
            }

            showAdminMessage(
                "Please log in as admin to load dashboard data.",
                true
            );

            return;
        }

        try {
            // Verify token using a protected admin endpoint.
            await adminApiRequest("/api/admin/leaderboard-status");

            if (authStatus) {
                authStatus.textContent = "ADMIN AUTHENTICATED";
                authStatus.style.color = "#8cf5c3";
            }

            await Promise.all([
                loadAdminParticipants(),
                loadAdminResults(),
                loadAdminRoundStatuses(),
                loadLeaderboardStatus()
            ]);
        } catch (error) {
            if (authStatus) {
                authStatus.textContent = "AUTHENTICATION FAILED";
                authStatus.style.color = "#ffb4b4";
            }

            showAdminMessage(
                `Admin verification failed: ${error.message}. Please log in again.`,
                true
            );
        }
    }

    initializeAdminDashboard();
});
