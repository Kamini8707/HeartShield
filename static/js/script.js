document.addEventListener("DOMContentLoaded", () => {
  // --- Configuration ---
  const quotes = [
    "The heart of a fool is in his mouth, but the mouth of a wise man is in his heart.",
    "A good heart is a beautiful home.",
    "Keep your heart healthy, it beats for you!",
    "Every beat counts. Processing your data...",
    "Health is the greatest gift.",
    "With a healthy heart, the beat goes on.",
  ];

  // --- DOM Elements ---
  const fileInput = document.getElementById("report-file");
  const uploadBtn = document.getElementById("upload-btn");
  const removeFileBtn = document.getElementById("remove-file-btn");

  // Preview & Zoom
  const previewContainer = document.getElementById("file-preview-container");
  const previewContent = document.getElementById("preview-content");
  const zoomInBtn = document.getElementById("zoom-in-btn");
  const zoomOutBtn = document.getElementById("zoom-out-btn");
  const zoomLevelText = document.getElementById("zoom-level");

  // Form & Results
  const uploadStatus = document.getElementById("upload-status");
  const manualForm = document.getElementById("manual-form");
  const clearBtn = document.getElementById("clear-btn");
  const resultsSection = document.getElementById("results-section");
  const hospitalSection = document.getElementById("hospital-section");
  const resultText = document.getElementById("result-text");
  const findHospitalsBtn = document.getElementById("find-hospitals-btn");

  // Overlays & Feedback
  const loadingOverlay = document.getElementById("loading-overlay");
  const loadingQuote = document.getElementById("loading-quote");
  const feedbackForm = document.getElementById("feedback-form");

  // Profile Pic Preview
  const profileUpload = document.getElementById("profile-upload");
  const profilePreview = document.getElementById("profile-preview");

  // Camera
  const startCameraBtn = document.getElementById("start-camera-btn");
  const cameraContainer = document.getElementById("camera-container");
  const videoFeed = document.getElementById("video-feed");
  const captureBtn = document.getElementById("capture-btn");
  const closeCameraBtn = document.getElementById("close-camera-btn");
  const canvas = document.getElementById("canvas");

  // Variables
  let quoteInterval;
  let currentZoom = 1.0;
  let capturedFile = null;
  let mediaStream = null;

  // --- 1. Event Listeners ---
  if (fileInput) fileInput.addEventListener("change", handleFileSelect);
  if (removeFileBtn) removeFileBtn.addEventListener("click", handleRemoveFile);
  if (uploadBtn) uploadBtn.addEventListener("click", handleReportUpload);
  if (clearBtn) clearBtn.addEventListener("click", handleClearAll);
  if (feedbackForm)
    feedbackForm.addEventListener("submit", handleFeedbackSubmit);

  if (zoomInBtn && zoomOutBtn) {
    zoomInBtn.addEventListener("click", () => updateZoom(0.1));
    zoomOutBtn.addEventListener("click", () => updateZoom(-0.1));
  }

  // Camera Listeners
  if (startCameraBtn) startCameraBtn.addEventListener("click", startCamera);
  if (captureBtn) captureBtn.addEventListener("click", captureImage);
  if (closeCameraBtn) closeCameraBtn.addEventListener("click", stopCamera);

  // Profile Pic Listener
  if (profileUpload && profilePreview) {
    profileUpload.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => (profilePreview.src = e.target.result);
        reader.readAsDataURL(file);
      }
    });
  }

  if (manualForm) {
    manualForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      // Only predict on button click
      if (manualForm.checkValidity()) {
        await handlePrediction();
      } else {
        manualForm.reportValidity();
        showStatus(
          resultText,
          "Please fill all required fields.",
          "error",
          resultsSection
        );
      }
    });

    // REMOVED: inputs.forEach listener.
    // Now, changing inputs manually will NOT trigger auto-prediction.
    // User MUST click "Analyse Risk".
  }

  // --- 2. Core Logic (Upload & Predict) ---

  async function handleReportUpload() {
    const file = capturedFile || fileInput.files[0];
    if (!file) {
      alert("Select a file first.");
      return;
    }

    // Clear previous results
    resultsSection.style.display = "none";
    hospitalSection.style.display = "none";
    resultText.innerHTML = "";

    const formData = new FormData();
    formData.append("file", file);

    showLoadingOverlay();
    uploadBtn.disabled = true;

    try {
      const response = await fetch("/extract", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Extraction Failed.");

      const data = await response.json();

      // Clear form before filling new data
      manualForm.reset();
      populateForm(data);

      // Manual Mode: Just show success message
      showStatus(
        uploadStatus,
        'Data extracted. Review fields and click "Analyse Risk".',
        "success"
      );
    } catch (error) {
      console.error(error);
      showStatus(uploadStatus, `Error: ${error.message}`, "error");
    } finally {
      hideLoadingOverlay();
      uploadBtn.disabled = false;
    }
  }

  async function handlePrediction() {
    const formData = new FormData(manualForm);
    const data = {};
    formData.forEach((val, key) => (data[key] = val));

    showStatus(resultText, "Analysing...", "loading", resultsSection);

    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Prediction failed.");
      }

      const result = await response.json();
      displayResults(result);

      if (result.probability > 50) {
        hospitalSection.style.display = "block";
        updateHospitalLink();
      } else {
        hospitalSection.style.display = "none";
      }
    } catch (error) {
      showStatus(resultText, error.message, "error", resultsSection);
    }
  }

  // --- 3. Smart Fill ---
  function populateForm(data) {
    const profile = typeof USER_PROFILE !== "undefined" ? USER_PROFILE : {};
    const has = (v) => v && String(v).trim().length > 0;
    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.value = v;
    };

    setVal(
      "age",
      has(data.age) ? data.age : has(profile.age) ? profile.age : ""
    );
    setVal(
      "height",
      has(data.height) ? data.height : has(profile.height) ? profile.height : ""
    );
    setVal(
      "weight",
      has(data.weight) ? data.weight : has(profile.weight) ? profile.weight : ""
    );

    if (has(data.gender) || has(profile.gender)) {
      const val = (data.gender || profile.gender).toLowerCase();
      document.getElementById("gender").value = val.startsWith("m")
        ? "male"
        : "female";
    }

    if (has(data.ap_hi)) setVal("ap_hi", data.ap_hi);
    if (has(data.ap_lo)) setVal("ap_lo", data.ap_lo);
    if (has(data.cholesterol)) setVal("cholesterol", data.cholesterol);
    if (has(data.glucose)) setVal("glucose", data.glucose);
    if (has(data.smoke)) setVal("smoke", data.smoke);
    if (has(data.alco)) setVal("alco", data.alco);
    if (has(data.active)) setVal("active", data.active);
  }

  // --- 4. Camera Functions ---
  async function startCamera() {
    fileInput.value = "";
    handleRemoveFile();
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      videoFeed.srcObject = mediaStream;
      cameraContainer.style.display = "block";
      startCameraBtn.style.display = "none";
    } catch (err) {
      alert("Camera access denied.");
    }
  }

  function stopCamera() {
    if (mediaStream) mediaStream.getTracks().forEach((t) => t.stop());
    cameraContainer.style.display = "none";
    startCameraBtn.style.display = "block";
  }

  function captureImage() {
    const ctx = canvas.getContext("2d");
    canvas.width = videoFeed.videoWidth;
    canvas.height = videoFeed.videoHeight;
    ctx.drawImage(videoFeed, 0, 0);
    canvas.toBlob((blob) => {
      capturedFile = new File([blob], "capture.jpg", { type: "image/jpeg" });
      showPreview(capturedFile);
      stopCamera();
    }, "image/jpeg");
  }

  // --- 5. Preview & Helper Functions ---
  function handleFileSelect(e) {
    capturedFile = null;
    const file = e.target.files[0];
    if (!file) return;
    showPreview(file);
  }

  function showPreview(file) {
    resetZoom();
    previewContainer.style.display = "block";
    previewContent.innerHTML = "";
    const url = URL.createObjectURL(file);

    if (file.type === "application/pdf") {
      const f = document.createElement("iframe");
      f.src = url;
      f.style.width = "100%";
      f.style.height = "500px";
      f.style.border = "none";
      previewContent.appendChild(f);
    } else {
      const i = document.createElement("img");
      i.src = url;
      i.style.maxWidth = "100%";
      i.style.display = "block";
      i.style.margin = "0 auto";
      previewContent.appendChild(i);
    }
  }

  function handleRemoveFile() {
    fileInput.value = "";
    capturedFile = null;
    previewContainer.style.display = "none";
    previewContent.innerHTML = "";
    uploadStatus.style.display = "none";
    stopCamera();
    resultsSection.style.display = "none";
    hospitalSection.style.display = "none";
    resultText.innerHTML = "";
  }

  function handleClearAll() {
    manualForm.reset();
    handleRemoveFile();
    resultsSection.style.display = "none";
    hospitalSection.style.display = "none";
    resultText.innerHTML = "";
  }

  function updateZoom(change) {
    currentZoom += change;
    if (currentZoom < 0.5) currentZoom = 0.5;
    if (currentZoom > 3.0) currentZoom = 3.0;
    previewContent.style.transform = `scale(${currentZoom})`;
    if (zoomLevelText)
      zoomLevelText.textContent = Math.round(currentZoom * 100) + "%";
  }

  function resetZoom() {
    currentZoom = 1.0;
    previewContent.style.transform = `scale(1)`;
    if (zoomLevelText) zoomLevelText.textContent = "100%";
  }

  function displayResults(result) {
    resultsSection.style.display = "block";
    let color =
      result.probability > 75
        ? "#dc3545"
        : result.probability > 50
        ? "#FFB74D"
        : "#28a745";
    let text =
      result.probability > 75
        ? "High Risk"
        : result.probability > 50
        ? "Moderate Risk"
        : "Low Risk";
    resultText.innerHTML = `<h3 style="color:${color}">${text}</h3><p style="font-size:1.2rem; font-weight:bold">Probability: ${result.probability}%</p>`;
  }

  function updateHospitalLink() {
    const btn = document.getElementById("find-hospitals-btn");
    if (!btn) return;

    // 1. Corrected Default Link
    const defaultUrl =
      "https://www.google.com/maps/search/cardiologist+near+me";
    btn.href = defaultUrl;

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          // 2. Corrected Geolocation Link
          const mapUrl = `https://www.google.com/maps/search/cardiologist/@${lat},${lng},13z`;
          btn.href = mapUrl;
        },
        (error) => {
          console.warn("Location access denied. Using default map.", error);
          btn.href = defaultUrl;
        }
      );
    }
  }

  function showLoadingOverlay() {
    if (!loadingOverlay) return;
    loadingOverlay.style.display = "flex";
    let i = 0;
    loadingQuote.textContent = quotes[0];
    loadingQuote.style.opacity = 1;
    quoteInterval = setInterval(() => {
      i = (i + 1) % quotes.length;
      loadingQuote.style.opacity = 0;
      setTimeout(() => {
        loadingQuote.textContent = quotes[i];
        loadingQuote.style.opacity = 1;
      }, 300);
    }, 2500);
  }

  function hideLoadingOverlay() {
    if (!loadingOverlay) return;
    loadingOverlay.style.display = "none";
    clearInterval(quoteInterval);
  }

  function showStatus(el, msg, type, container = null) {
    el.innerHTML = msg;
    el.className = `status-message status-${type}`;
    el.style.display = "block";
    if (container) container.style.display = "block";
  }

  async function handleFeedbackSubmit(e) {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const review = document.getElementById("review").value;
    const statusDiv = document.getElementById("feedback-status");
    if (!review) {
      showStatus(statusDiv, "Please enter a review.", "error");
      return;
    }
    showStatus(statusDiv, "Submitting...", "loading");

    try {
      const response = await fetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, review }),
      });
      if (response.ok) {
        showStatus(statusDiv, "Thank you for your feedback!", "success");
        document.getElementById("feedback-form").reset();
      } else {
        showStatus(statusDiv, "Error submitting feedback.", "error");
      }
    } catch (err) {
      showStatus(statusDiv, "Network error.", "error");
    }
  }
});
