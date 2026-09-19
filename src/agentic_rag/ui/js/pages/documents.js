import { api } from "../api.js";
import { formatDate, formatSize } from "../format.js";
import { showToast } from "../toast.js";

const statusColors = { processed: "success", failed: "danger", uploaded: "secondary" };

export const title = "Documents";

export function render(container) {
  container.innerHTML = `
    <div class="card mb-3">
      <div class="card-header"><h3 class="card-title">Upload a PDF</h3></div>
      <div class="card-body">
        <form id="upload-form" class="row g-2 align-items-center">
          <div class="col">
            <input type="file" class="form-control" id="file" accept=".pdf,application/pdf" required />
          </div>
          <div class="col-auto">
            <button type="submit" class="btn btn-primary" id="upload">
              <i class="ti ti-upload me-1"></i>Upload
            </button>
          </div>
        </form>
        <div class="text-secondary small mt-2">
          The text is extracted and embeddings are made, so big files can take some time.
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Uploaded documents</h3>
        <div class="card-actions">
          <button class="btn btn-sm" id="reload"><i class="ti ti-refresh me-1"></i>Reload</button>
        </div>
      </div>
      <div class="table-responsive">
        <table class="table table-vcenter card-table">
          <thead>
            <tr>
              <th>Name</th><th>Pages</th><th>Chunks</th><th>Size</th><th>Status</th><th>Uploaded</th><th></th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </div>`;

  const rows = container.querySelector("#rows");
  const form = container.querySelector("#upload-form");
  const fileInput = container.querySelector("#file");
  const uploadButton = container.querySelector("#upload");

  async function loadDocuments() {
    rows.innerHTML = messageRow("Loading...");
    try {
      const documents = await api("/documents");
      rows.innerHTML = "";
      if (documents.length === 0) {
        rows.innerHTML = messageRow("No documents yet. Upload a PDF to start.");
      }
      documents.forEach((document) => rows.append(documentRow(document, loadDocuments)));
    } catch (error) {
      rows.innerHTML = messageRow(error.message);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) {
      return;
    }

    const body = new FormData();
    body.append("file", file);
    uploadButton.disabled = true;
    uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
    try {
      const result = await api("/documents", { method: "POST", body });
      showToast(`${result.filename} uploaded with ${result.chunk_count} chunks`);
      form.reset();
    } catch (error) {
      showToast(error.message, "danger");
    } finally {
      uploadButton.disabled = false;
      uploadButton.innerHTML = '<i class="ti ti-upload me-1"></i>Upload';
      loadDocuments();
    }
  });

  container.querySelector("#reload").addEventListener("click", loadDocuments);
  loadDocuments();
}

function messageRow(text) {
  const row = document.createElement("tr");
  row.innerHTML = '<td colspan="7" class="text-center text-secondary py-4"></td>';
  row.firstChild.textContent = text;
  return row.outerHTML;
}

function documentRow(document_, reload) {
  const row = document.createElement("tr");
  const cells = [
    document_.filename,
    document_.page_count ?? "-",
    document_.chunk_count,
    formatSize(document_.size_bytes),
  ];
  cells.forEach((value) => {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.append(cell);
  });

  const statusCell = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = `badge text-white bg-${statusColors[document_.status] || "secondary"}`;
  badge.textContent = document_.status;
  statusCell.append(badge);
  row.append(statusCell);

  const dateCell = document.createElement("td");
  dateCell.className = "text-secondary";
  dateCell.textContent = formatDate(document_.created_at);
  row.append(dateCell);

  const actionCell = document.createElement("td");
  actionCell.className = "text-end";
  const deleteButton = document.createElement("button");
  deleteButton.className = "btn btn-sm btn-outline-danger";
  deleteButton.innerHTML = '<i class="ti ti-trash me-1"></i>Delete';
  deleteButton.addEventListener("click", async () => {
    if (!confirm(`Delete "${document_.filename}" and all its chunks?`)) {
      return;
    }
    deleteButton.disabled = true;
    try {
      await api(`/documents/${document_.id}`, { method: "DELETE" });
      showToast(`${document_.filename} deleted`);
    } catch (error) {
      showToast(error.message, "danger");
    }
    reload();
  });
  actionCell.append(deleteButton);
  row.append(actionCell);

  return row;
}
