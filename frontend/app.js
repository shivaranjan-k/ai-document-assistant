const chatContainer = document.getElementById("chatContainer");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");

// Keep stable session ID per browser using localStorage
let sessionId = localStorage.getItem("rag_session_id");
if (!sessionId) {
    sessionId = "session_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now();
    localStorage.setItem("rag_session_id", sessionId);
}
const fileInput = document.getElementById("fileInput");
const uploadButton = document.getElementById("uploadButton");

const documentsList =
    document.getElementById("documentsList");

const refreshDocuments =
    document.getElementById("refreshDocuments");

refreshDocuments.addEventListener(
    "click",
    loadDocuments
);

loadDocuments();

uploadButton.addEventListener("click", function () {
    console.log("UPLOAD BUTTON CLICKED");
    fileInput.click();
});

fileInput.addEventListener("change", function () {

    console.log("FILE SELECTED");

    if (fileInput.files.length > 0) {
        console.log("Selected file:", fileInput.files[0].name);
        uploadPDF(fileInput.files[0]);
    }

});

sendButton.addEventListener("click", sendQuestion);


questionInput.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {
        sendQuestion();
    }

});


async function sendQuestion() {

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }


    // Show user message
    addMessage(question, "user");


    // Clear input
    questionInput.value = "";


    // Disable button while processing
    sendButton.disabled = true;


    // Create empty assistant message
    const assistantMessage = addMessage("", "assistant");


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/ask/stream",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    session_id: sessionId,
                    question: question
                })
            }
        );


        if (!response.ok) {
            throw new Error("Server error");
        }


        // Read streaming response
        const reader = response.body.getReader();

        const decoder = new TextDecoder();

        let buffer = "";


        while (true) {

            const { value, done } = await reader.read();

            if (done) {
                break;
            }


            buffer += decoder.decode(value, {
                stream: true
            });


            // SSE events are separated by blank lines
            const events = buffer.split("\n\n");


            // Keep incomplete event for next chunk
            buffer = events.pop();


            for (const event of events) {

                if (!event.startsWith("data:")) {
                    continue;
                }


                const jsonString = event
                    .replace("data:", "")
                    .trim();


                const data = JSON.parse(jsonString);


                // LLM token
                if (data.type === "token") {

                    assistantMessage.textContent += data.content;

                    chatContainer.scrollTop =
                        chatContainer.scrollHeight;
                }
                if (data.type === "answer") {
    assistantMessage.textContent = data.content;
    chatContainer.scrollTop = chatContainer.scrollHeight;
}


                // Sources
                if (data.type === "sources") {

                    displaySources(
                        assistantMessage,
                        data.sources
                    );
                }

            }

        }


    } catch (error) {

        console.error(error);

        assistantMessage.textContent =
            "❌ Unable to connect to the AI server.";

    }


    sendButton.disabled = false;

    questionInput.focus();
}


function addMessage(text, sender) {

    const message = document.createElement("div");

    message.className = `message ${sender}`;


    const content = document.createElement("div");

    content.className = "message-content";

    content.textContent = text;


    message.appendChild(content);

    chatContainer.appendChild(message);


    chatContainer.scrollTop =
        chatContainer.scrollHeight;


    return content;
}


function displaySources(messageElement, sources) {

    if (!sources || sources.length === 0) {
        return;
    }

    const sourcesContainer =
        document.createElement("div");

    sourcesContainer.className = "sources-container";


    const sourcesHeader =
        document.createElement("button");

    sourcesHeader.className = "sources-header";

    sourcesHeader.innerHTML = `
        <span>📚 Sources (${sources.length})</span>
        <span class="sources-arrow rotate">▲</span>
    `;


    const sourcesList =
        document.createElement("div");

    sourcesList.className = "sources-list show";


    sources.forEach(source => {

        const sourceCard =
            document.createElement("a");

        sourceCard.className = "source-card";

        // Create URL for the PDF
        const pdfUrl =
            `http://127.0.0.1:8000/documents/${encodeURIComponent(source.source)}#page=${source.page}`;

        sourceCard.href = pdfUrl;

        sourceCard.target = "_blank";

        sourceCard.rel = "noopener noreferrer";


        // Safe DOM rendering for source card
        const iconDiv = document.createElement("div");
        iconDiv.className = "source-icon";
        iconDiv.textContent = "📄";

        const infoDiv = document.createElement("div");
        infoDiv.className = "source-info";

        const nameDiv = document.createElement("div");
        nameDiv.className = "source-name";
        nameDiv.textContent = source.source;

        const pageDiv = document.createElement("div");
        pageDiv.className = "source-page";
        pageDiv.textContent = `Page ${source.page}`;

        infoDiv.appendChild(nameDiv);
        infoDiv.appendChild(pageDiv);

        const arrowDiv = document.createElement("div");
        arrowDiv.className = "source-arrow";
        arrowDiv.textContent = "→";

        sourceCard.appendChild(iconDiv);
        sourceCard.appendChild(infoDiv);
        sourceCard.appendChild(arrowDiv);

        sourcesList.appendChild(sourceCard);

    });


    sourcesHeader.addEventListener("click", function () {

        sourcesList.classList.toggle("show");

        const arrow =
            sourcesHeader.querySelector(".sources-arrow");

        arrow.classList.toggle("rotate");

        arrow.textContent =
            sourcesList.classList.contains("show")
                ? "▲"
                : "▼";
    });


    sourcesContainer.appendChild(sourcesHeader);

    sourcesContainer.appendChild(sourcesList);

    messageElement.appendChild(sourcesContainer);
}
async function uploadPDF(file) {
       console.log("UPLOAD FUNCTION CALLED");
       console.log("Selected file:", file);

        console.log("uploadPDF() called:", file.name);

    if (!file.name.toLowerCase().endsWith(".pdf")) {

        

        alert("Please select a PDF file.");

        return;
    }

    uploadButton.disabled = true;

    uploadButton.textContent = "Uploading...";

    const formData = new FormData();

    formData.append("file", file);

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/upload",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.message || data.error || "Upload failed"
            );
        }

        alert(
            `✅ ${file.name} uploaded successfully!\n\n` +
            `${data.chunks} chunks added to the knowledge base.`
        );

        // Refresh document list after successful upload
        loadDocuments();

    } catch (error) {

        console.error(error);

        alert(
            "❌ Upload failed: " + error.message
        );

    } finally {

        uploadButton.disabled = false;

        uploadButton.textContent = "📤 Upload PDF";

        fileInput.value = "";

    }
}
async function loadDocuments() {
    const documentsList = document.getElementById("documentsList");

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/api/documents"
        );

        if (!response.ok) {
            throw new Error("Failed to load documents");
        }

        const data = await response.json();

        documentsList.innerHTML = "";

        if (data.documents.length === 0) {
            documentsList.innerHTML =
                '<div class="empty-documents">No documents uploaded.</div>';
            return;
        }

        data.documents.forEach(filename => {

            const item = document.createElement("div");
            item.className = "document-item";

            // PDF icon
            const icon = document.createElement("span");
            icon.className = "document-icon";
            icon.textContent = "📄";

            // File name
            const name = document.createElement("span");
            name.className = "document-name";
            name.textContent = filename;

            // Delete button
            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-document";
            deleteButton.textContent = "🗑️";
            deleteButton.title = "Delete document";

            deleteButton.addEventListener("click", function () {
                deleteDocument(filename);
            });

            item.appendChild(icon);
            item.appendChild(name);
            item.appendChild(deleteButton);

            documentsList.appendChild(item);
        });

    } catch (error) {

        console.error(error);

        documentsList.innerHTML =
            "❌ Unable to load documents.";
    }
}
async function deleteDocument(filename) {

    const confirmed = confirm(
        `Are you sure you want to delete "${filename}"?`
    );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `http://127.0.0.1:8000/api/documents/${encodeURIComponent(filename)}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message || "Delete failed"
            );
        }

        alert(`✅ ${filename} deleted successfully.`);

        // Reload document list
        loadDocuments();

    } catch (error) {

        console.error(error);

        alert(
            `❌ Failed to delete ${filename}: ${error.message}`
        );
    }
}