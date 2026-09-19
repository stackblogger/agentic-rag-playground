export function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast show align-items-center text-bg-${type} border-0`;
  toast.setAttribute("role", "alert");

  const row = document.createElement("div");
  row.className = "d-flex";
  const body = document.createElement("div");
  body.className = "toast-body";
  body.textContent = message;
  const close = document.createElement("button");
  close.type = "button";
  close.className = "btn-close btn-close-white me-2 m-auto";
  close.addEventListener("click", () => toast.remove());
  row.append(body, close);
  toast.append(row);

  document.getElementById("toasts").append(toast);
  setTimeout(() => toast.remove(), 4000);
}
