/* =================================================================
   Ship It — landing page behavior
   ----------------------------------------------------------------
   CONFIG: edit these two lines to go fully live.
   ================================================================= */
const CONFIG = {
  // Paste your Formspree endpoint here to start collecting emails.
  //   1. Make a free form at https://formspree.io
  //   2. Copy the endpoint, e.g. "https://formspree.io/f/abcdwxyz"
  //   3. Replace the value below.
  // Leave it as "" to skip email collection — the download still works.
  formEndpoint: "",

  // Where the actual product lives. Drop your real PDF at this path
  // (keep the filename) and the button just works.
  downloadPath: "downloads/ebook.pdf",
};

/* ----------------------------------------------------------------- */

const form = document.getElementById("signup-form");
const emailInput = document.getElementById("email");
const submitBtn = document.getElementById("submit-btn");
const errorEl = document.getElementById("form-error");
const successEl = document.getElementById("success");
const downloadLink = document.getElementById("download-link");

// Point the download button(s) at the configured file.
if (downloadLink) downloadLink.setAttribute("href", CONFIG.downloadPath);

const isValidEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
  emailInput.setAttribute("aria-invalid", "true");
}

function clearError() {
  errorEl.hidden = true;
  emailInput.removeAttribute("aria-invalid");
}

function revealDownload() {
  form.hidden = true;
  successEl.hidden = false;
  // Nudge the file to start downloading automatically.
  successEl.scrollIntoView({ behavior: "smooth", block: "center" });
  try {
    downloadLink.click();
  } catch (_) {
    /* user can click the button manually */
  }
}

emailInput.addEventListener("input", clearError);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = emailInput.value.trim();

  if (!isValidEmail(email)) {
    showError("Please enter a valid email address.");
    emailInput.focus();
    return;
  }

  clearError();
  submitBtn.disabled = true;
  submitBtn.textContent = "Sending…";

  // If a form endpoint is configured, save the email. If the request
  // fails (or none is set), we still let people download — no dead ends.
  if (CONFIG.formEndpoint) {
    try {
      await fetch(CONFIG.formEndpoint, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
    } catch (_) {
      /* fall through to the download anyway */
    }
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Send me the guide";
  revealDownload();
});

// Footer year.
const yearEl = document.getElementById("year");
if (yearEl) yearEl.textContent = new Date().getFullYear();
