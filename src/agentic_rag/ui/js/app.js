import * as documents from "./pages/documents.js";
import * as status from "./pages/status.js";

const pages = {
  documents: { ...documents, label: "Documents", icon: "ti-files" },
  status: { ...status, label: "Status", icon: "ti-heartbeat" },
};

const defaultPage = "documents";

function currentPage() {
  const name = location.hash.replace("#/", "");
  return pages[name] ? name : defaultPage;
}

function renderNav(active) {
  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  for (const [name, page] of Object.entries(pages)) {
    const item = document.createElement("li");
    item.className = `nav-item${name === active ? " active" : ""}`;
    item.innerHTML = `
      <a class="nav-link" href="#/${name}">
        <span class="nav-link-icon"><i class="ti ${page.icon}"></i></span>
        <span class="nav-link-title">${page.label}</span>
      </a>`;
    nav.append(item);
  }
}

function renderPage() {
  const name = currentPage();
  const page = pages[name];
  renderNav(name);
  document.title = `${page.title} - Agentic RAG Playground`;
  document.getElementById("page-title").textContent = page.title;

  const container = document.getElementById("page");
  container.innerHTML = "";
  page.render(container);
}

window.addEventListener("hashchange", renderPage);
renderPage();
