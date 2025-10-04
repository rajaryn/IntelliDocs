// static/script.js (with Zoom Limits)

import * as pdfjsLib from "https://mozilla.github.io/pdf.js/build/pdf.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = `https://mozilla.github.io/pdf.js/build/pdf.worker.mjs`;

const pdfViewer = document.getElementById("pdf-viewer");
const pdfUrl = pdfViewer ? pdfViewer.dataset.url : null;
const canvas = document.getElementById("pdf-canvas");
const context = canvas ? canvas.getContext("2d") : null;
const loadingSpinner = document.getElementById("loading-spinner");

// --- STATE MANAGEMENT ---
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.0;

// --- 1. NEW CONSTANTS FOR ZOOM LIMITS ---
const MIN_SCALE = 0.5;
const MAX_SCALE = 3.0;

// --- LOGIC ---
async function renderPage(num) {
  pageRendering = true;
  loadingSpinner.style.display = "block";
  canvas.style.display = "none";

  try {
    const page = await pdfDoc.getPage(num);
    const viewport = page.getViewport({ scale: scale });
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    canvas.style.height = `${viewport.height}px`;
    canvas.style.width = `${viewport.width}px`;

    const renderContext = { canvasContext: context, viewport: viewport };
    await page.render(renderContext).promise;
  } catch (error) {
    console.error("Error during page rendering:", error);
  }

  pageRendering = false;
  loadingSpinner.style.display = "none";
  canvas.style.display = "block";

  document.getElementById("page-num").textContent = num;

  if (pageNumPending !== null) {
    renderPage(pageNumPending);
    pageNumPending = null;
  }
}

function queueRenderPage(num) {
  if (pageRendering) {
    pageNumPending = num;
  } else {
    renderPage(num);
  }
}

// --- 3. NEW HELPER FUNCTION TO UPDATE BUTTON STATE ---
function updateZoomControls() {
  document.getElementById("zoom-in").disabled = scale >= MAX_SCALE;
  document.getElementById("zoom-out").disabled = scale <= MIN_SCALE;
}

// --- EVENT LISTENERS ---
document.getElementById("prev-page").addEventListener("click", () => {
  if (pageNum <= 1) return;
  pageNum--;
  queueRenderPage(pageNum);
});

document.getElementById("next-page").addEventListener("click", () => {
  if (pageNum >= pdfDoc.numPages) return;
  pageNum++;
  queueRenderPage(pageNum);
});

// --- 2. UPDATED ZOOM LISTENERS WITH LIMITS ---
document.getElementById("zoom-in").addEventListener("click", () => {
  if (scale >= MAX_SCALE) return; // Check against max scale
  scale += 0.25;
  document.getElementById("zoom-percent").textContent = Math.round(scale * 100);
  queueRenderPage(pageNum);
  updateZoomControls(); // Update button state
});

document.getElementById("zoom-out").addEventListener("click", () => {
  if (scale <= MIN_SCALE) return; // Check against min scale
  scale -= 0.25;
  document.getElementById("zoom-percent").textContent = Math.round(scale * 100);
  queueRenderPage(pageNum);
  updateZoomControls(); // Update button state
});

// --- INITIALIZATION ---
(async function () {
  try {
    if (!pdfUrl) {
      console.error("CRITICAL ERROR: pdfUrl is empty or null.");
      return;
    }
    pdfDoc = await pdfjsLib.getDocument(pdfUrl).promise;
    document.getElementById("page-count").textContent = pdfDoc.numPages;
    document.getElementById("zoom-percent").textContent = Math.round(
      scale * 100
    );
    renderPage(pageNum);
    updateZoomControls(); // Set the initial state of the buttons
  } catch (error) {
    console.error("Error loading PDF:", error);
    loadingSpinner.style.display = "none";
    document.getElementById("pdf-viewer").textContent =
      "Error: Failed to load PDF document.";
  }
})();
