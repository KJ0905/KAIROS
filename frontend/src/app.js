
const API_BASE = "";

const state = {
    candidateId: null,
    conversationId: null,
    isLoading: false
};

const $ = (selector) => document.querySelector(selector);

const themeToggle = $("#theme-toggle");
const themeIcon = $("#theme-icon");
const themeLabel = $("#theme-label");

const sidebar = $("#sidebar");
const jobPanel = $("#job-panel");
const welcome = $("#welcome");
const chatMessages = $("#chat-messages");
const chatForm = $("#chat-form");
const questionInput = $("#question");
const sendButton = $("#send-btn");
const stopButton = $("#stop-button");
let activeChatController = null;
let activeStreamReader = null;
let stopRequested = false;
const uploadInput = $("#resume-upload");
const uploadStatus = $("#upload-status");
const candidateList = $("#candidate-list");
const jobDescription = $("#job-description");
const matchStatus = $("#match-status");
const matchResults = $("#match-results");

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;

    try {
        localStorage.setItem("portfolio-ai-theme", theme);
    } catch (error) {
        console.warn("Unable to save theme preference.");
    }

    if (themeIcon) {
        themeIcon.textContent = theme === "dark" ? "☀" : "☾";
    }

    if (themeLabel) {
        themeLabel.textContent =
            theme === "dark" ? "Light mode" : "Dark mode";
    }
}

let savedTheme = "light";

try {
    savedTheme = localStorage.getItem("portfolio-ai-theme") || "light";
} catch (error) {
    console.warn("Unable to read saved theme.");
}

applyTheme(savedTheme === "dark" ? "dark" : "light");

themeToggle?.addEventListener("click", () => {
    const currentTheme = document.documentElement.dataset.theme;
    applyTheme(currentTheme === "dark" ? "light" : "dark");
});

$("#job-panel-toggle")?.addEventListener("click", () => {
    if (jobPanel) {
        jobPanel.hidden = !jobPanel.hidden;
    }
});

$("#job-panel-close")?.addEventListener("click", () => {
    if (jobPanel) {
        jobPanel.hidden = true;
    }
});


const app = document.querySelector(".app");

function toggleSidebar() {
    if (window.matchMedia("(min-width: 761px)").matches) {
        app?.classList.toggle("sidebar-collapsed");
    } else {
        sidebar?.classList.toggle("open");
    }
}

$("#sidebar-toggle")?.addEventListener("click", toggleSidebar);
$("#mobile-menu")?.addEventListener("click", toggleSidebar);


const whyHireBtn = document.getElementById("why-hire-btn");

whyHireBtn?.addEventListener("click", () => {
    const question = document.getElementById("question");

    if (!question) return;

    question.value = "Why should we hire this candidate?";
    question.dispatchEvent(new Event("input", { bubbles: true }));

    document.getElementById("chat-form")?.requestSubmit();
});

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function renderMarkdown(text) {
    const codeBlocks = [];
    const tableBlocks = [];

    let html = String(text ?? "")
        .replace(/\r\n?/g, "\n")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .trim()
        .replace(/```([^\n]*)\n([\s\S]*?)(?:```|$)/g, (_, language, code) => {
            const index = codeBlocks.length;
            const safeLanguage = escapeHTML(language.trim().split(/\s+/)[0] || "text");
            codeBlocks.push(
                `<pre><code class="language-${safeLanguage}">${escapeHTML(code.replace(/\n$/, ""))}</code></pre>`
            );
            return `\n@@CODEBLOCK${index}@@\n`;
        });

    html = escapeHTML(html);

    // Inline formatting
    html = html
        .replace(/`([^`\n]+)`/g, "<code>$1</code>")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/__(.+?)__/g, "<strong>$1</strong>")
        .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>")
        .replace(/(?<!_)_([^_\n]+)_(?!_)/g, "<em>$1</em>");

    
    // Convert Markdown links safely.
    html = html.replace(
        /\[([^\]\n]+)\]\((https?:\/\/[^)\s]+|mailto:[^)\s]+)\)/gi,
        (_, label, url) =>
            `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`
    );

    // Convert angle-bracket URLs into clickable links.
    html = html.replace(
        /&lt;(https?:\/\/[^&\s]+)&gt;/gi,
        (_, url) =>
            `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
    );

    // Convert plain URLs, but never URLs already inside an HTML attribute.
    html = html.replace(
        /(?<!["'=])(https?:\/\/[^\s<>&"']+)/gi,
        (url) => {
            const cleanUrl = url.replace(/[.,!?;:)]+$/, "");
            const trailing = url.slice(cleanUrl.length);

            return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer">${cleanUrl}</a>${trailing}`;
        }
    );


    const lines = html.split("\n");
    const output = [];
    let paragraph = [];
    let listType = null;

    function flushParagraph() {
        if (paragraph.length) {
            output.push(`<p>${paragraph.join(" ")}</p>`);
            paragraph = [];
        }
    }

    function closeList() {
        if (listType) {
            output.push(`</${listType}>`);
            listType = null;
        }
    }

    function parseTable(start) {
        const header = lines[start].trim();
        const separator = lines[start + 1]?.trim();

        if (
            !header.includes("|") ||
            !separator ||
            !/^\|?[\s:|-]+\|?$/.test(separator) ||
            !separator.includes("-")
        ) {
            return null;
        }

        const cells = (line) =>
            line.trim().replace(/^\|/, "").replace(/\|$/, "")
                .split("|").map((cell) => cell.trim());

        const headings = cells(header);
        const rows = [];

        let i = start + 2;
        while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
            rows.push(cells(lines[i]));
            i++;
        }

        const thead = `<thead><tr>${headings.map(
            (cell) => `<th>${cell}</th>`
        ).join("")}</tr></thead>`;

        const tbody = rows.length
            ? `<tbody>${rows.map((row) =>
                `<tr>${headings.map((_, index) =>
                    `<td>${row[index] || ""}</td>`
                ).join("")}</tr>`
            ).join("")}</tbody>`
            : "";

        return {
            html: `<div class="table-wrapper"><table>${thead}${tbody}</table></div>`,
            next: i
        };
    }

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        const codeMarker = trimmed.match(/^@@CODEBLOCK(\d+)@@$/);
        const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
        const unordered = trimmed.match(/^[-*+]\s+(.+)$/);
        const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
        const quote = trimmed.match(/^&gt;\s?(.*)$/);
        const table = parseTable(i);

        if (!trimmed) {
            flushParagraph();
            closeList();
            continue;
        }

        if (codeMarker) {
            flushParagraph();
            closeList();
            output.push(`@@CODEBLOCK${codeMarker[1]}@@`);
            continue;
        }

        if (table) {
            flushParagraph();
            closeList();
            output.push(table.html);
            i = table.next - 1;
            continue;
        }

        if (heading) {
            flushParagraph();
            closeList();
            const level = heading[1].length;
            output.push(`<h${level}>${heading[2]}</h${level}>`);
            continue;
        }

        if (quote) {
            flushParagraph();
            closeList();
            output.push(`<blockquote>${quote[1]}</blockquote>`);
            continue;
        }

        if (unordered || ordered) {
            flushParagraph();
            const type = unordered ? "ul" : "ol";

            if (listType !== type) {
                closeList();
                output.push(`<${type}>`);
                listType = type;
            }

            output.push(`<li>${(unordered || ordered)[1]}</li>`);
            continue;
        }

        closeList();
        paragraph.push(line);
    }

    flushParagraph();
    closeList();

    html = output.join("\n");

    html = html.replace(/@@CODEBLOCK(\d+)@@/g, (_, index) =>
        codeBlocks[Number(index)] || ""
    );

    return html;
}

// function addMessage(role, content) {
//     const message = document.createElement("div");
//     message.className = `message ${role}`;

//     const avatar = document.createElement("div");
//     avatar.className = "message-avatar";
//     //avatar.textContent = role === "user" ? "YOU" : "AI";

//     const body = document.createElement("div");
//     body.className = "message-content";

//     if (role === "assistant") {
//         body.innerHTML = renderMarkdown(content);
//     } else {
//         body.textContent = content;
//     }

//     message.append(avatar, body);
//     chatMessages.appendChild(message);
//     chatMessages.scrollTop = chatMessages.scrollHeight;

//     return message;
// }


function addMessage(role, content) {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const body = document.createElement("div");
    body.className = "message-content";

    if (role === "assistant") {
        body.innerHTML = renderMarkdown(content);

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";

        message.append(avatar, body);
    } else {
        body.textContent = content;
        message.appendChild(body);
    }

    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return message;
}


function setLoading(loading) {
    state.isLoading = loading;

    if (sendButton) {
        sendButton.disabled = loading;
    }

    if (questionInput) {
        questionInput.disabled = loading;
    }

    if (sendButton) {
        sendButton.textContent = loading ? "…" : "↑";
    }
}

async function readJsonResponse(response) {
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.detail || data.message || "Something went wrong."
        );
    }

    return data;
}


async function loadCandidates() {
    try {
        const response = await fetch(`${API_BASE}/api/portfolio`);
        const data = await readJsonResponse(response);

        candidateList.replaceChildren();

        if (!data.available) {
            candidateList.textContent = "Portfolio resume not uploaded yet.";
            return;
        }

        const item = document.createElement("div");
        item.className = "candidate-item";

        const name = document.createElement("div");
        name.textContent = data.name || "Portfolio Owner";
        name.className = "candidate-name";

        const skills = document.createElement("div");
        skills.textContent = (data.skills || []).join(", ");
        skills.className = "candidate-skills";

        item.append(name, skills);
        candidateList.appendChild(item);
    } catch (error) {
        console.error("Could not load portfolio:", error);
        candidateList.textContent = "Could not load portfolio.";
    }
}


async function selectCandidate() {
    state.conversationId = null;
    chatMessages.replaceChildren();

    if (welcome) {
        welcome.hidden = false;
    }

    sidebar?.classList.remove("open");

    try {
        const response = await fetch(`${API_BASE}/api/conversations`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({})
        });

        const data = await readJsonResponse(response);
        state.conversationId = data.conversation_id;

        addMessage(
            "assistant",
            "Hi! I'm your portfolio assistant. Ask me about my skills, experience, projects, education, or suitability for a role."
        );
    } catch (error) {
        console.error("Failed to create conversation:", error);

        addMessage(
            "assistant",
            error.message || "Couldn't start a conversation. Please try again."
        );
    }
}


let conversationPromise = null;

async function ensureConversation() {
    if (state.conversationId) {
        return state.conversationId;
    }

    if (!conversationPromise) {
        conversationPromise = (async () => {
            const response = await fetch(`${API_BASE}/api/conversations`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({})
            });

            const data = await readJsonResponse(response);
            state.conversationId = data.conversation_id;

            return state.conversationId;
        })().finally(() => {
            conversationPromise = null;
        });
    }

    return conversationPromise;
}


uploadInput?.addEventListener("change", async () => {
    const file = uploadInput.files?.[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        uploadStatus.textContent = "Please upload a PDF resume.";
        uploadInput.value = "";
        return;
    }

    uploadStatus.textContent = "Uploading resume...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_BASE}/api/admin/resume`, {
            method: "POST",
            body: formData,
            credentials: "same-origin"
        });

        const data = await readJsonResponse(response);

        uploadStatus.textContent =
            data.message || "Resume uploaded successfully.";

        await loadCandidates();
    } catch (error) {
        console.error("Resume upload failed:", error);
        uploadStatus.textContent =
            error.message || "Resume upload failed.";
    } finally {
        uploadInput.value = "";
    }
});


async function sendMessage() {
    const question = questionInput.value.trim();

    if (!question || state.isLoading) return;

    try {
        await ensureConversation();
    } catch (error) {
        console.error("Failed to initialize conversation:", error);
        addMessage("assistant", "Couldn't start a conversation. Please try again.");
        return;
    }

    if (!state.conversationId) {
        console.error("Conversation ID is still missing.");
        return;
    }


    const welcomeSection = document.getElementById("welcome");

    if (welcomeSection) {
        welcomeSection.hidden = true;
    }

    addMessage("user", question);
    questionInput.value = "";
    setLoading(true);
    sendButton.hidden = true;
    stopButton.hidden = false;

    const answerMessage = addMessage("assistant", "Thinking...");
    const messageContent = answerMessage.querySelector(".message-content");
    stopRequested = false;
    activeChatController = new AbortController();

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            signal: activeChatController.signal,
            body: JSON.stringify({
                conversation_id: state.conversationId,
                question: question
            })
        });

        if (!response.ok) {
            await readJsonResponse(response);
        }

        if (!response.body) {
            throw new Error("The server returned an empty response.");
        }

        const reader = response.body.getReader();
        activeStreamReader = reader;
        const decoder = new TextDecoder();

        let buffer = "";
        let answer = "";
        let displayDone = false;
        let streamError = null;

        const displayQueue = [];
        let queueIndex = 0;
        let charIndex = 0;

        function enqueueText(text) {
            if (typeof text !== "string" || !text) return;

            answer += text;
            displayQueue.push(...text);
        }

        function processSSEBlock(block) {
            if (stopRequested) return;
            const lines = block.split(/\r?\n/);
            let eventName = "";
            const dataLines = [];

            for (const line of lines) {
                if (line.startsWith("event:")) {
                    eventName = line.slice(6).trim();
                } else if (line.startsWith("data:")) {
                    dataLines.push(line.slice(5).trimStart());
                }
            }

            if (dataLines.length === 0) return;

            const dataText = dataLines.join("\n");

            if (dataText.trim() === "[DONE]") return;

            let payload;

            try {
                payload = JSON.parse(dataText);
            } catch {
                enqueueText(dataText);
                return;
            }

            if (eventName === "error" || payload.error) {
                throw new Error(
                    payload.error || payload.message || dataText
                );
            }

            const chunk =
                payload.token ??
                payload.content ??
                payload.text ??
                payload.answer ??
                "";

            enqueueText(chunk);
        }

        
const displayTask = (async () => {
    let displayedText = "";

    while (
        !displayDone ||
        (!stopRequested && queueIndex < displayQueue.length)
    ) {
        if (document.hidden) {
            // Drain received text quickly while the tab is hidden.
            while (queueIndex < displayQueue.length && !stopRequested) {
                //if (stopRequested) break;
                displayedText += displayQueue[queueIndex];
                queueIndex++;
            }

            // Avoid repeatedly updating the hidden DOM.
            await new Promise(resolve => setTimeout(resolve, 50));
            continue;
        }

        if (queueIndex < displayQueue.length) {
            if (stopRequested) break;
            displayedText += displayQueue[queueIndex];
            queueIndex++;

            messageContent.innerHTML = renderMarkdown(displayedText);

            chatMessages.scrollTop = chatMessages.scrollHeight;

            await new Promise(resolve => setTimeout(resolve, 8));
        } else {
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        // Show the accumulated text when the tab becomes visible.
        if (!document.hidden) {
            messageContent.innerHTML = renderMarkdown(displayedText);
        }
    }

    // Render the complete response as Markdown after streaming.
    if (!stopRequested) {
        messageContent.innerHTML = renderMarkdown(answer);
    }
})();


        try {
            while (true) {
                const { value, done } = await reader.read();

                if (done || stopRequested) break;

                buffer += decoder.decode(value, { stream: true });

                const blocks = buffer.split(/\r?\n\r?\n/);
                buffer = blocks.pop() || "";

                for (const block of blocks) {
                    processSSEBlock(block);
                }
            }

            buffer += decoder.decode();

            if (buffer.trim()) {
                processSSEBlock(buffer);
            }
        } catch (error) {
            streamError = error;
        } finally {
            displayDone = true;
            await displayTask;
        }

        if (streamError) {
            throw streamError;
        }
        if (stopRequested) {
            // Keep only the text already displayed.
            return;
        }
        if (!answer.trim()) {
            messageContent.textContent =
                "I couldn't generate a response. Please try again.";
        } else {
            messageContent.innerHTML = renderMarkdown(answer);
        }

    } catch (error) {
        if (error.name === "AbortError") {
            if (!messageContent.textContent.trim() ||
                messageContent.textContent === "Thinking...") {
                messageContent.textContent = "Response stopped.";
            }
        } else {
            console.error("Chat request failed:", error);

            messageContent.textContent =
                `Error: ${error.message || "Unable to get a response."}`;
        }
    } finally {
        activeChatController = null;
        activeStreamReader = null;

        setLoading(false);
        sendButton.hidden = false;
        stopButton.hidden = true;

        questionInput.focus();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

stopButton.addEventListener("click", async () => {
    if (!activeChatController) return;

    stopRequested = true;

    // Immediately discard all queued characters.
    displayQueue.length = 0;
    queueIndex = 0;

    // Stop the network request.
    activeChatController.abort();

    // Cancel the reader if it exists.
    if (activeStreamReader) {
        try {
            await activeStreamReader.cancel();
        } catch (error) {
            console.debug("Stream cancellation:", error);
        }
    }
});

chatForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage();
});

$("#new-chat-btn")?.addEventListener("click", async () => {
    try {
        const response = await fetch(`${API_BASE}/api/conversations`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({})
        });

        const data = await readJsonResponse(response);

        state.conversationId = data.conversation_id;
        chatMessages.replaceChildren();

        if (welcome) {
            welcome.hidden = false;
        }

        questionInput.focus();
    } catch (error) {
        console.error("Could not start a new chat:", error);
        alert(error.message || "Could not start a new chat.");
    }

    sidebar?.classList.remove("open");
});

document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", async () => {
        const prompt =
            button.dataset.prompt ||
            button.dataset.question ||
            button.textContent.trim();

        if (!prompt || state.isLoading) return;

        questionInput.value = prompt;
        await sendMessage();
    });
});

$("#match-btn")?.addEventListener("click", async () => {
    const description = jobDescription.value.trim();

    // if (!state.conversationId) {
    //     matchStatus.textContent = "Please start a chat first.";
    //     return;
    // }

    if (!description) {
        matchStatus.textContent = "Enter a job description first.";
        return;
    }

    matchStatus.textContent = "Analyzing job match...";
    matchResults.replaceChildren();

        try {
            const response = await fetch(`${API_BASE}/api/job-match`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    job_description: description
            })
        });


        const data = await readJsonResponse(response);

        matchStatus.textContent = "Analysis complete.";

        const score = data.score ?? data.match_score;

        if (score !== undefined) {
            const scoreElement = document.createElement("h3");
            scoreElement.textContent = `Match score: ${score}%`;
            matchResults.appendChild(scoreElement);
        }

        const sections = [
            ["Matched skills", data.matched_skills || data.matching_skills],
            ["Missing skills", data.missing_skills],
            ["Recommendations", data.recommendations]
        ];

        sections.forEach(([heading, items]) => {
            if (!items || items.length === 0) return;

            const section = document.createElement("section");
            const title = document.createElement("h4");
            title.textContent = heading;
            section.appendChild(title);

            if (Array.isArray(items)) {
                const list = document.createElement("ul");

                items.forEach((item) => {
                    const li = document.createElement("li");
                    li.textContent =
                        typeof item === "string"
                            ? item
                            : JSON.stringify(item);
                    list.appendChild(li);
                });

                section.appendChild(list);
            } else {
                const paragraph = document.createElement("p");
                paragraph.textContent = String(items);
                section.appendChild(paragraph);
            }

            matchResults.appendChild(section);
        });

        if (!matchResults.children.length) {
            const result = document.createElement("pre");
            result.textContent = JSON.stringify(data, null, 2);
            matchResults.appendChild(result);
        }
    } catch (error) {
        console.error("Job matching failed:", error);
        matchStatus.textContent =
            error.message || "Unable to analyze this job description.";
    }
});

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

loadCandidates();
ensureConversation().catch(console.error);

// Admin panel
const adminPanel = document.getElementById("admin-panel");
const adminOpenBtn = document.getElementById("admin-open-btn");
const adminLoginForm = document.getElementById("admin-login-form");
const adminUsername = document.getElementById("admin-username");
const adminPassword = document.getElementById("admin-password");
const adminStatus = document.getElementById("admin-status");
const adminResumeControls = document.getElementById("admin-resume-controls");
const adminResumeUpload = document.getElementById("admin-resume-upload");
const adminUploadStatus = document.getElementById("admin-upload-status");
const adminDeleteResume = document.getElementById("admin-delete-resume");
const adminLogoutBtn = document.getElementById("admin-logout-btn");
// Personal Knowledge Base elements
const personalProfileForm = document.getElementById("personal-profile-form");
const personalProfileStatus = document.getElementById("personal-profile-status");
const deletePersonalProfileBtn = document.getElementById("delete-personal-profile");

const profileFields = {
    introduction: document.getElementById("profile-introduction"),
    personality: document.getElementById("profile-personality"),
    strengths: document.getElementById("profile-strengths"),
    improvements: document.getElementById("profile-improvements"),
    softSkills: document.getElementById("profile-soft-skills"),
    communication: document.getElementById("profile-communication"),
    teamwork: document.getElementById("profile-teamwork"),
    leadership: document.getElementById("profile-leadership"),
    problemSolving: document.getElementById("profile-problem-solving"),
    adaptability: document.getElementById("profile-adaptability"),

    experienceTitle: document.getElementById("profile-experience-title"),
    experienceSituation: document.getElementById("profile-experience-situation"),
    experienceAction: document.getElementById("profile-experience-action"),
    experienceResult: document.getElementById("profile-experience-result"),
    experienceSkills: document.getElementById("profile-experience-skills"),

    workStyle: document.getElementById("profile-work-style"),
    preferredRoles: document.getElementById("profile-preferred-roles"),
    careerGoals: document.getElementById("profile-career-goals"),
};

// Preserve experience stories beyond the first one
let additionalPersonalExperiences = [];
function linesToArray(value) {
    return value
        .split("\n")
        .map(item => item.trim())
        .filter(item => item.length > 0);
}


function arrayToLines(value) {
    return Array.isArray(value) ? value.join("\n") : "";
}


function clearPersonalProfileForm() {
    Object.values(profileFields).forEach(field => {
        if (field) {
            field.value = "";
        }
    });

    additionalPersonalExperiences = [];
}


function populatePersonalProfile(profile) {
    profileFields.introduction.value = profile.introduction || "";

    profileFields.personality.value = arrayToLines(profile.personality_traits);
    profileFields.strengths.value = arrayToLines(profile.strengths);
    profileFields.improvements.value = arrayToLines(profile.areas_to_improve);
    profileFields.softSkills.value = arrayToLines(profile.soft_skills);

    profileFields.communication.value = arrayToLines(profile.communication);
    profileFields.teamwork.value = arrayToLines(profile.teamwork);
    profileFields.leadership.value = arrayToLines(profile.leadership);
    profileFields.problemSolving.value = arrayToLines(profile.problem_solving);
    profileFields.adaptability.value = arrayToLines(profile.adaptability_and_learning);

    profileFields.workStyle.value = arrayToLines(profile.work_style);
    profileFields.preferredRoles.value = arrayToLines(profile.preferred_roles);
    profileFields.careerGoals.value = arrayToLines(profile.career_goals);

    const experiences = profile.experiences || [];
    const firstExperience = experiences[0] || {};

    profileFields.experienceTitle.value = firstExperience.title || "";
    profileFields.experienceSituation.value = firstExperience.situation || "";
    profileFields.experienceAction.value = firstExperience.action || "";
    profileFields.experienceResult.value = firstExperience.result || "";
    profileFields.experienceSkills.value = arrayToLines(
        firstExperience.skills_demonstrated
    );

    // Keep remaining experiences so saving does not erase them.
    additionalPersonalExperiences = experiences.slice(1);
}
async function loadPersonalProfile() {
    try {
        const response = await fetch("/api/admin/personal-profile");

        if (!response.ok) {
            throw new Error("Could not load personal knowledge.");
        }

        const data = await response.json();

        populatePersonalProfile(data.profile);

        personalProfileStatus.textContent =
            "Personal knowledge loaded successfully.";

    } catch (error) {
        personalProfileStatus.textContent = error.message;
        console.error("Load personal profile error:", error);
    }
}


async function savePersonalProfile(event) {
    event.preventDefault();

    personalProfileStatus.textContent = "Saving...";

    const experienceTitle = profileFields.experienceTitle.value.trim();

    const currentExperience = experienceTitle
        ? [{
            title: experienceTitle,
            situation: profileFields.experienceSituation.value.trim() || null,
            action: profileFields.experienceAction.value.trim() || null,
            result: profileFields.experienceResult.value.trim() || null,
            skills_demonstrated: linesToArray(
                profileFields.experienceSkills.value
            )
        }]
        : [];

    const profile = {
        introduction: profileFields.introduction.value.trim() || null,

        personality_traits: linesToArray(profileFields.personality.value),
        strengths: linesToArray(profileFields.strengths.value),
        areas_to_improve: linesToArray(profileFields.improvements.value),
        soft_skills: linesToArray(profileFields.softSkills.value),

        communication: linesToArray(profileFields.communication.value),
        teamwork: linesToArray(profileFields.teamwork.value),
        leadership: linesToArray(profileFields.leadership.value),
        problem_solving: linesToArray(profileFields.problemSolving.value),
        adaptability_and_learning: linesToArray(
            profileFields.adaptability.value
        ),

        experiences: [
            ...currentExperience,
            ...additionalPersonalExperiences
        ],

        work_style: linesToArray(profileFields.workStyle.value),
        preferred_roles: linesToArray(profileFields.preferredRoles.value),
        career_goals: linesToArray(profileFields.careerGoals.value)
    };

    try {
        const response = await fetch("/api/admin/personal-profile", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(profile)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to save personal knowledge.");
        }

        populatePersonalProfile(data.profile);

        personalProfileStatus.textContent =
            "Personal knowledge saved successfully!";

    } catch (error) {
        personalProfileStatus.textContent = error.message;
        console.error("Save personal profile error:", error);
    }
}


async function removePersonalProfile() {
    const confirmed = confirm(
        "Are you sure you want to delete all personal knowledge?"
    );

    if (!confirmed) return;

    personalProfileStatus.textContent = "Deleting...";

    try {
        const response = await fetch("/api/admin/personal-profile", {
            method: "DELETE"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to delete personal knowledge.");
        }

        clearPersonalProfileForm();

        personalProfileStatus.textContent =
            "Personal knowledge deleted successfully.";

    } catch (error) {
        personalProfileStatus.textContent = error.message;
        console.error("Delete personal profile error:", error);
    }
}
if (personalProfileForm) {
    personalProfileForm.addEventListener(
        "submit",
        savePersonalProfile
    );
}

if (deletePersonalProfileBtn) {
    deletePersonalProfileBtn.addEventListener(
        "click",
        removePersonalProfile
    );
}

async function refreshAdminStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/status`, {
            credentials: "same-origin"
        });

        const data = await readJsonResponse(response);
        const authenticated = data.authenticated === true;

        adminLoginForm.hidden = authenticated;
        adminResumeControls.hidden = !authenticated;

        adminStatus.textContent = authenticated
            ? "Logged in as admin."
            : "Log in to manage your portfolio resume.";

        if (authenticated) {
            const portfolioResponse = await fetch(
                `${API_BASE}/api/admin/portfolio`,
                { credentials: "same-origin" }
            );

            const portfolio = await readJsonResponse(portfolioResponse);

            adminUploadStatus.textContent = portfolio.available
                ? `Current resume: ${portfolio.original_filename}`
                : "No resume uploaded yet.";

            await loadPersonalProfile();
        }
    } catch (error) {
        console.error("Could not check admin session:", error);
        adminStatus.textContent = "Could not check admin login status.";
    }
}

adminOpenBtn?.addEventListener("click", async () => {
    adminPanel.hidden = !adminPanel.hidden;

    if (!adminPanel.hidden) {
        await refreshAdminStatus();
        sidebar?.classList.add("open");
    }
});

adminLoginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    adminStatus.textContent = "Logging in...";

    try {
        const response = await fetch(`${API_BASE}/api/admin/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                username: adminUsername.value,
                password: adminPassword.value
            })
        });

        const data = await readJsonResponse(response);

        adminPassword.value = "";
        adminStatus.textContent = data.message || "Login successful.";

        await refreshAdminStatus();
    } catch (error) {
        console.error("Admin login failed:", error);
        adminStatus.textContent = error.message || "Login failed.";
    }
});

adminResumeUpload?.addEventListener("change", async () => {
    const file = adminResumeUpload.files?.[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        adminUploadStatus.textContent = "Please select a PDF file.";
        adminResumeUpload.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    adminUploadStatus.textContent = "Uploading resume...";

    try {
        const response = await fetch(`${API_BASE}/api/admin/resume`, {
            method: "POST",
            credentials: "same-origin",
            body: formData
        });

        const data = await readJsonResponse(response);

        adminUploadStatus.textContent =
            data.message || "Resume uploaded successfully.";

        await loadCandidates();
        await refreshAdminStatus();
    } catch (error) {
        console.error("Resume upload failed:", error);
        adminUploadStatus.textContent =
            error.message || "Resume upload failed.";
    } finally {
        adminResumeUpload.value = "";
    }
});

adminDeleteResume?.addEventListener("click", async () => {
    const confirmed = confirm(
        "Delete your portfolio resume and all saved chat history? This cannot be undone."
    );

    if (!confirmed) return;

    adminUploadStatus.textContent = "Deleting portfolio resume...";

    try {
        const response = await fetch(`${API_BASE}/api/admin/resume`, {
            method: "DELETE",
            credentials: "same-origin"
        });

        const data = await readJsonResponse(response);

        adminUploadStatus.textContent =
            data.message || "Portfolio resume deleted.";

        await loadCandidates();
        await refreshAdminStatus();
    } catch (error) {
        console.error("Resume deletion failed:", error);
        adminUploadStatus.textContent =
            error.message || "Could not delete resume.";
    }
});

adminLogoutBtn?.addEventListener("click", async () => {
    try {
        const response = await fetch(`${API_BASE}/api/admin/logout`, {
            method: "POST",
            credentials: "same-origin"
        });

        await readJsonResponse(response);
        await refreshAdminStatus();
        adminStatus.textContent = "You have logged out.";
    } catch (error) {
        console.error("Admin logout failed:", error);
        adminStatus.textContent = error.message || "Logout failed.";
    }
});

// Restore the admin session state when the page loads.
refreshAdminStatus();

