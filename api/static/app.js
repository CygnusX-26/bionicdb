const escapeHtml = (value) => String(value ?? "—").replace(
  /[&<>'"]/g,
  (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character],
);

const MATCHES_STORAGE_KEY = "bionicdb-matches";
const OFFSET_STORAGE_KEY = "bionicdb-offset";

function readStoredResult(key) {
  try {
    return JSON.parse(localStorage.getItem(key));
  } catch (_) {
    return null;
  }
}

function storeResult(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (_) {
    // The query still works if storage is unavailable or full.
  }
}

async function request(path) {
  let response;
  try {
    response = await fetch(path);
  } catch (_) {
    throw new Error("Could not reach the API.");
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try { message = (await response.json()).detail || message; } catch (_) { /* no JSON body */ }
    throw new Error(message);
  }
  return response;
}

function setBusy(form, busy) {
  form.querySelector("button").disabled = busy;
}

function showError(result, error) {
  result.innerHTML = `<div class="message error">${escapeHtml(error.message)}</div>`;
}

const sortableColumns = [
  ["name", "Symbol"],
  ["build_id", "Build ID (click to download)"],
  ["device", "Device"],
  ["android_version", "Android"],
  ["android_api", "API"],
];

function sortButton(key, label, sort) {
  const active = sort.key === key;
  const ariaSort = active ? (sort.direction === "asc" ? "ascending" : "descending") : "none";
  const upActive = active && sort.direction === "asc" ? " active" : "";
  const downActive = active && sort.direction === "desc" ? " active" : "";
  return `<th aria-sort="${ariaSort}"><button class="sort-button" type="button" data-sort="${key}">${label}<span class="sort-icon" aria-hidden="true"><span class="sort-up${upActive}">▲</span><span class="sort-down${downActive}">▼</span></span></button></th>`;
}

function renderMatches(result, rows, sort = { key: null, direction: "asc" }) {
  const sortedRows = [...rows];
  if (sort.key) {
    sortedRows.sort((left, right) => {
      const leftValue = left[sort.key] ?? "";
      const rightValue = right[sort.key] ?? "";
      const comparison = ["android_version", "android_api"].includes(sort.key)
        ? Number(leftValue) - Number(rightValue)
        : String(leftValue).localeCompare(String(rightValue), undefined, { numeric: true, sensitivity: "base" });
      return sort.direction === "asc" ? comparison : -comparison;
    });
  }

  const headings = Object.fromEntries(sortableColumns.map(([key, label]) => [key, sortButton(key, label, sort)]));
  result.innerHTML = `<div class="table-wrap"><table>
    <thead><tr>${headings.name}<th>Offset</th>${headings.build_id}${headings.device}${headings.android_version}${headings.android_api}</tr></thead>
    <tbody>${sortedRows.map((row) => `<tr>
      <td class="mono">${escapeHtml(row.name)}</td>
      <td class="mono">0x${Number(row.offset).toString(16)}</td>
      <td class="mono"><a href="/v1/libs/${encodeURIComponent(row.build_id)}" download="${escapeHtml(row.build_id)}.so">${escapeHtml(row.build_id)}</a></td>
      <td>${escapeHtml(row.device)}</td>
      <td>${escapeHtml(row.android_version)}</td>
      <td>${escapeHtml(row.android_api)}</td>
    </tr>`).join("")}</tbody>
  </table></div>`;

  result.querySelectorAll("[data-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      const direction = sort.key === key && sort.direction === "asc" ? "desc" : "asc";
      renderMatches(result, rows, { key, direction });
    });
  });

  const form = document.querySelector("#matches-form");
  storeResult(MATCHES_STORAGE_KEY, {
    offset: form.elements.offset.value,
    symbol: form.elements.symbol.value,
    rows,
    sort,
  });
}

document.querySelector("#matches-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = document.querySelector("#matches-result");
  const values = new FormData(form);
  const params = new URLSearchParams({ offset: values.get("offset").trim() });
  const symbol = values.get("symbol").trim();
  if (symbol) params.set("symbol", symbol);
  setBusy(form, true);

  try {
    const data = await (await request(`/v1/symbol/matches?${params}`)).json();
    if (!data.libs.length) {
      result.innerHTML = '<div class="message">No matches.</div>';
      storeResult(MATCHES_STORAGE_KEY, {
        offset: values.get("offset").trim(),
        symbol,
        rows: [],
        sort: { key: null, direction: "asc" },
      });
      return;
    }
    renderMatches(result, data.libs);
  } catch (error) { showError(result, error); }
  finally { setBusy(form, false); }
});

document.querySelector("#offset-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = document.querySelector("#offset-result");
  const values = new FormData(form);
  const buildId = values.get("buildId").trim();
  const params = new URLSearchParams({ symbol: values.get("symbol").trim() });
  setBusy(form, true);

  try {
    const data = await (await request(`/v1/libs/${encodeURIComponent(buildId)}/offset?${params}`)).json();
    result.innerHTML = `<div class="message">Offset: <span class="value">${escapeHtml(data.offset)}</span></div>`;
    storeResult(OFFSET_STORAGE_KEY, {
      buildId,
      symbol: values.get("symbol").trim(),
      offset: data.offset,
    });
  } catch (error) { showError(result, error); }
  finally { setBusy(form, false); }
});

const storedMatches = readStoredResult(MATCHES_STORAGE_KEY);
if (storedMatches && Array.isArray(storedMatches.rows)) {
  const form = document.querySelector("#matches-form");
  form.elements.offset.value = storedMatches.offset ?? "";
  form.elements.symbol.value = storedMatches.symbol ?? "";
  const result = document.querySelector("#matches-result");
  if (storedMatches.rows.length) {
    renderMatches(
      result,
      storedMatches.rows,
      storedMatches.sort ?? { key: null, direction: "asc" },
    );
  } else {
    result.innerHTML = '<div class="message">No matches.</div>';
  }
}

const storedOffset = readStoredResult(OFFSET_STORAGE_KEY);
if (storedOffset?.offset) {
  const form = document.querySelector("#offset-form");
  form.elements.buildId.value = storedOffset.buildId ?? "";
  form.elements.symbol.value = storedOffset.symbol ?? "";
  document.querySelector("#offset-result").innerHTML = `<div class="message">Offset: <span class="value">${escapeHtml(storedOffset.offset)}</span></div>`;
}
