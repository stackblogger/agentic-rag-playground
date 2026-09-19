export async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(formatError(data) || `Request failed (${response.status})`);
  }
  return data;
}

function formatError(data) {
  if (!data || !data.detail) {
    return "";
  }
  if (typeof data.detail === "string") {
    return data.detail;
  }
  // validation errors from FastAPI come as a list
  return data.detail.map((item) => item.msg).join(", ");
}
