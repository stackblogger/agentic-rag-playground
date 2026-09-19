// The LLM answer can have text from the documents, so the HTML is cleaned before it is shown.
if (window.DOMPurify) {
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.tagName === "A") {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener noreferrer");
    }
  });
}

export function renderMarkdown(element, text) {
  if (!window.marked || !window.DOMPurify) {
    // libraries did not load (for example no internet), show plain text
    element.textContent = text;
    return;
  }
  // images are not allowed, because loading an image from a link can send data to another site
  const html = DOMPurify.sanitize(marked.parse(text, { breaks: true }), { FORBID_TAGS: ["img"] });
  element.innerHTML = html;
}
