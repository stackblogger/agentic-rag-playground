import { api } from "../api.js";
import { showToast } from "../toast.js";

export const title = "Search";

export function render(container) {
  container.innerHTML = `
    <div class="card mb-3">
      <div class="card-body">
        <form id="search-form" class="row g-2 align-items-center">
          <div class="col">
            <input type="text" class="form-control" id="query" placeholder="Search inside the documents..." required />
          </div>
          <div class="col-auto">
            <select class="form-select" id="limit" title="Number of results">
              <option value="3">3 results</option>
              <option value="5" selected>5 results</option>
              <option value="10">10 results</option>
              <option value="20">20 results</option>
            </select>
          </div>
          <div class="col-auto">
            <button type="submit" class="btn btn-primary" id="search">
              <i class="ti ti-search me-1"></i>Search
            </button>
          </div>
        </form>
        <div class="text-secondary small mt-2">
          The search is done by meaning, so the words in the query do not need to match the text exactly.
        </div>
      </div>
    </div>
    <div id="results"></div>`;

  const form = container.querySelector("#search-form");
  const queryInput = container.querySelector("#query");
  const limitSelect = container.querySelector("#limit");
  const searchButton = container.querySelector("#search");
  const results = container.querySelector("#results");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = queryInput.value.trim();
    if (!query) {
      return;
    }

    searchButton.disabled = true;
    searchButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Searching...';
    try {
      const params = new URLSearchParams({ query, limit: limitSelect.value });
      const found = await api(`/search?${params}`);
      showResults(results, found);
    } catch (error) {
      showToast(error.message, "danger");
    } finally {
      searchButton.disabled = false;
      searchButton.innerHTML = '<i class="ti ti-search me-1"></i>Search';
    }
  });

  queryInput.focus();
}

function showResults(results, found) {
  results.innerHTML = "";
  if (found.length === 0) {
    const empty = document.createElement("div");
    empty.className = "text-center text-secondary py-5";
    empty.textContent = "Nothing found. Upload some documents first, or try different words.";
    results.append(empty);
    return;
  }
  found.forEach((item, index) => results.append(resultCard(item, index + 1)));
}

function resultCard(item, position) {
  const card = document.createElement("div");
  card.className = "card mb-3";
  card.innerHTML = `
    <div class="card-header">
      <h3 class="card-title"><span class="text-secondary me-2" data-position></span><i class="ti ti-file-text me-1"></i><span data-filename></span></h3>
      <div class="card-actions">
        <span class="badge bg-secondary-lt me-1" data-page></span>
        <span class="badge text-white bg-primary" data-score></span>
      </div>
    </div>
    <div class="card-body"><div class="result-text" data-content></div></div>`;

  card.querySelector("[data-position]").textContent = `#${position}`;
  card.querySelector("[data-filename]").textContent = item.filename;
  card.querySelector("[data-page]").textContent = `Page ${item.page_number ?? "-"}`;
  card.querySelector("[data-score]").textContent = `Score ${item.score.toFixed(2)}`;
  card.querySelector("[data-content]").textContent = item.content;
  return card;
}
