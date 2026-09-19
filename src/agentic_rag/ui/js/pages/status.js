import { api } from "../api.js";

const checks = [
  { name: "API", path: "/health", icon: "ti-server" },
  { name: "Database", path: "/health/db", icon: "ti-database" },
];

export const title = "Status";

export function render(container) {
  container.innerHTML = `
    <div class="row row-cards" id="status-cards"></div>
    <div class="mt-3">
      <button class="btn btn-primary" id="refresh">
        <i class="ti ti-refresh me-1"></i>Check again
      </button>
    </div>`;

  const cards = container.querySelector("#status-cards");
  const load = () => {
    cards.innerHTML = "";
    checks.forEach((check) => cards.append(statusCard(check)));
  };
  container.querySelector("#refresh").addEventListener("click", load);
  load();
}

function statusCard({ name, path, icon }) {
  const col = document.createElement("div");
  col.className = "col-md-6";
  col.innerHTML = `
    <div class="card status-card">
      <div class="card-body d-flex align-items-center">
        <i class="ti ${icon} status-icon me-3 text-secondary"></i>
        <div>
          <div class="fw-bold">${name}</div>
          <div class="text-secondary small" data-message>Checking...</div>
        </div>
        <span class="badge text-white bg-secondary ms-auto" data-badge>...</span>
      </div>
    </div>`;

  const badge = col.querySelector("[data-badge]");
  const message = col.querySelector("[data-message]");
  api(path)
    .then(() => {
      badge.className = "badge text-white bg-success ms-auto";
      badge.textContent = "OK";
      message.textContent = "Working fine";
    })
    .catch((error) => {
      badge.className = "badge text-white bg-danger ms-auto";
      badge.textContent = "Down";
      message.textContent = error.message;
    });
  return col;
}
