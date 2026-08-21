document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const deptFilter = document.getElementById("department-filter");

    function addMessage(text, sender, sources = null, stats = null) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", sender);
        
        // Main text
        const textDiv = document.createElement("div");
        // Simple markdown parsing for bold
        textDiv.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n/g, '<br>');
        msgDiv.appendChild(textDiv);

        // Sources
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.classList.add("sources");
            sourcesDiv.innerHTML = "<strong>Sources:</strong><ul>" + 
                sources.map(s => `<li>${s.document} &rarr; ${s.section} (Page ${s.page})</li>`).join("") +
                "</ul>";
            msgDiv.appendChild(sourcesDiv);
        }

        // Stats
        if (stats) {
            const statsDiv = document.createElement("div");
            statsDiv.classList.add("stats");
            statsDiv.textContent = `Retrieval: ${stats.bm25_results} BM25 | ${stats.vector_results} Vector | ${stats.reranked_results} Reranked`;
            msgDiv.appendChild(statsDiv);
        }

        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        const department = deptFilter.value;

        // Add user message to UI
        addMessage(text, "user");
        userInput.value = "";
        
        // Disable input while loading
        userInput.disabled = true;
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query: text,
                    department: department
                })
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();
            addMessage(data.answer, "ai", data.sources, data.retrieval);

        } catch (error) {
            console.error("Chat error:", error);
            addMessage("Sorry, I encountered an error while processing your request.", "system");
        } finally {
            // Re-enable input
            userInput.disabled = false;
            sendBtn.disabled = false;
            sendBtn.textContent = "Send";
            userInput.focus();
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});
