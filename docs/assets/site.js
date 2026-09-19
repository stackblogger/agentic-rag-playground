const themeButton = document.getElementById("theme");
const docContainer = document.getElementById("doc");
const docCache = {};

// ---------- theme ----------
themeButton.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem("theme", next);
  } catch (error) {
    // the theme is still changed for this visit
  }
});

// ---------- copy buttons and quick start tabs ----------
document.querySelectorAll(".copy").forEach((button) => {
  button.addEventListener("click", async () => {
    const text = button.parentElement.querySelector("code").innerText;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "Copied!";
    } catch (error) {
      button.textContent = "Press Ctrl+C";
    }
    setTimeout(() => (button.textContent = "Copy"), 1800);
  });
});

document.querySelectorAll("#start-tabs .tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#start-tabs .tab").forEach((other) => other.classList.toggle("active", other === tab));
    document.querySelectorAll("#start-docker, #start-local").forEach((box) => {
      box.classList.toggle("hidden", box.id !== tab.dataset.target);
    });
  });
});

// ---------- highlight the code blocks ----------
if (window.hljs) {
  document.querySelectorAll(".code pre code").forEach((block) => hljs.highlightElement(block));
}

// ---------- docs viewer (shows the markdown files of the repo) ----------
const docFiles = { architecture: "architecture.md", api: "api.md", database: "database.md" };

async function showDoc(name) {
  if (!docFiles[name]) {
    name = "architecture";
  }
  document.querySelectorAll("#doc-tabs .tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.doc === name));

  try {
    if (!docCache[name]) {
      const response = await fetch(docFiles[name]);
      if (!response.ok) {
        throw new Error(`Status ${response.status}`);
      }
      docCache[name] = await response.text();
    }
    renderMarkdown(docCache[name]);
  } catch (error) {
    docContainer.innerHTML = "";
    const message = document.createElement("div");
    message.className = "md-message";
    message.innerHTML = `Could not load this doc. <a href="https://github.com/stackblogger/agentic-rag-playground/blob/main/docs/${docFiles[name]}" target="_blank" rel="noopener">Open it on GitHub</a>.`;
    docContainer.append(message);
  }
}

function renderMarkdown(text) {
  if (!window.marked || !window.DOMPurify) {
    docContainer.textContent = text;
    return;
  }
  docContainer.innerHTML = DOMPurify.sanitize(marked.parse(text), { FORBID_TAGS: ["img"] });
  docContainer.querySelectorAll("table").forEach((table) => {
    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    table.replaceWith(wrap);
    wrap.append(table);
  });
  if (window.hljs) {
    docContainer.querySelectorAll("pre code").forEach((block) => {
      // the plain text diagrams have no language, so they are left as they are
      if (block.className.includes("language-")) {
        hljs.highlightElement(block);
      }
    });
  }
}

document.querySelectorAll("#doc-tabs .tab").forEach((tab) => {
  tab.addEventListener("click", () => showDoc(tab.dataset.doc));
});

// links in the page that open a doc, like the one under the architecture picture
document.querySelectorAll("a[data-doc]").forEach((link) => {
  link.addEventListener("click", () => showDoc(link.dataset.doc));
});

showDoc("architecture");

// ---------- mark the menu link of the section on screen ----------
const links = [...document.querySelectorAll("#nav a")];
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        links.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`));
      }
    });
  },
  { rootMargin: "-45% 0px -50% 0px" }
);
links.forEach((link) => {
  const section = document.querySelector(link.getAttribute("href"));
  if (section) {
    observer.observe(section);
  }
});
