const escapeHtml = (value) => String(value ?? "—").replace(
  /[&<>'"]/g,
  (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character],
);

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
      return;
    }
    result.innerHTML = `<div class="table-wrap"><table>
      <thead><tr><th>Symbol</th><th>Offset</th><th>Build ID</th><th>Device</th><th>Android</th><th>API</th><th>Security patch</th></tr></thead>
      <tbody>${data.libs.map((row) => `<tr>
        <td class="mono">${escapeHtml(row.name)}</td>
        <td class="mono">0x${Number(row.offset).toString(16)}</td>
        <td class="mono">${escapeHtml(row.build_id)}</td>
        <td>${escapeHtml(row.device)}</td>
        <td>${escapeHtml(row.android_version)}</td>
        <td>${escapeHtml(row.android_api)}</td>
        <td>${escapeHtml(row.security_patch)}</td>
      </tr>`).join("")}</tbody>
    </table></div>`;
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
  } catch (error) { showError(result, error); }
  finally { setBusy(form, false); }
});

document.querySelector("#download-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = document.querySelector("#download-result");
  const buildId = new FormData(form).get("buildId").trim();
  setBusy(form, true);

  try {
    const blob = await (await request(`/v1/libs/${encodeURIComponent(buildId)}`)).blob();
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement("a"), { href: url, download: `${buildId}.so` });
    link.click();
    URL.revokeObjectURL(url);
    result.innerHTML = '<div class="message">Download started.</div>';
  } catch (error) { showError(result, error); }
  finally { setBusy(form, false); }
});
