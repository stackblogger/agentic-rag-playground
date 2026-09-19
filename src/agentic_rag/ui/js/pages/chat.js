import { api } from "../api.js";
import { renderMarkdown } from "../markdown.js";
import { showToast } from "../toast.js";

export const title = "Chat";

const welcomeText = "Ask a question about the uploaded documents. The answer is made from what is found in them.";

export function render(container) {
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Chat with the documents</h3>
        <div class="card-actions">
          <button class="btn btn-sm" id="clear"><i class="ti ti-eraser me-1"></i>Clear</button>
        </div>
      </div>
      <div class="card-body chat-thread" id="thread"></div>
      <div class="card-footer">
        <form id="chat-form" class="row g-2 align-items-center">
          <div class="col">
            <input type="text" class="form-control" id="question" placeholder="Type your question..." required />
          </div>
          <div class="col-auto">
            <select class="form-select" id="limit" title="Chunks used from each search">
              <option value="3">3 chunks</option>
              <option value="5" selected>5 chunks</option>
              <option value="10">10 chunks</option>
            </select>
          </div>
          <div class="col-auto">
            <button type="submit" class="btn btn-primary" id="send">
              <i class="ti ti-send me-1"></i>Send
            </button>
          </div>
        </form>
        <div class="text-secondary small mt-2">Each question is answered on its own. Earlier questions are not remembered.</div>
      </div>
    </div>`;

  const thread = container.querySelector("#thread");
  const form = container.querySelector("#chat-form");
  const questionInput = container.querySelector("#question");
  const limitSelect = container.querySelector("#limit");
  const sendButton = container.querySelector("#send");

  function showWelcome() {
    thread.innerHTML = "";
    const welcome = document.createElement("div");
    welcome.className = "text-center text-secondary py-4";
    welcome.textContent = welcomeText;
    welcome.id = "welcome";
    thread.append(welcome);
  }

  function addMessage(node) {
    thread.querySelector("#welcome")?.remove();
    thread.append(node);
    thread.scrollTop = thread.scrollHeight;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = questionInput.value.trim();
    if (!question) {
      return;
    }

    addMessage(userMessage(question));
    questionInput.value = "";
    const waiting = waitingMessage();
    addMessage(waiting);
    sendButton.disabled = true;
    try {
      const result = await api("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, limit: Number(limitSelect.value) }),
      });
      waiting.replaceWith(answerMessage(result));
    } catch (error) {
      waiting.remove();
      showToast(error.message, "danger");
    } finally {
      sendButton.disabled = false;
      thread.scrollTop = thread.scrollHeight;
      questionInput.focus();
    }
  });

  container.querySelector("#clear").addEventListener("click", showWelcome);
  showWelcome();
  questionInput.focus();
}

function userMessage(text) {
  const row = document.createElement("div");
  row.className = "chat-row chat-row-user";
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble chat-bubble-user";
  bubble.textContent = text;
  row.append(bubble);
  return row;
}

function waitingMessage() {
  const row = document.createElement("div");
  row.className = "chat-row";
  row.innerHTML = `
    <div class="chat-bubble chat-bubble-bot text-secondary">
      <span class="spinner-border spinner-border-sm me-2"></span>Searching the documents...
    </div>`;
  return row;
}

function answerMessage(result) {
  const row = document.createElement("div");
  row.className = "chat-row";
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble chat-bubble-bot";

  const answer = document.createElement("div");
  answer.className = "chat-answer";
  renderMarkdown(answer, result.answer);
  bubble.append(answer);

  const seen = new Set();
  const sources = result.sources.filter((source) => {
    const key = `${source.document_id}-${source.page_number}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });

  if (sources.length > 0) {
    const list = document.createElement("div");
    list.className = "mt-2 pt-2 border-top";
    const label = document.createElement("span");
    label.className = "text-secondary small me-2";
    label.textContent = "Sources:";
    list.append(label);
    sources.forEach((source) => {
      const badge = document.createElement("span");
      badge.className = "badge bg-secondary-lt me-1";
      badge.textContent = `${source.filename}, page ${source.page_number ?? "-"}`;
      list.append(badge);
    });
    bubble.append(list);
  }

  row.append(bubble);
  return row;
}
