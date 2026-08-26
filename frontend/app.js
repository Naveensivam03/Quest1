const API_URL = "http://127.0.0.1:8000";

const videoUrlInput = document.getElementById("video-url");
const dialogueInput = document.getElementById("dialogue");
const findButton = document.getElementById("find-button");

const status = document.getElementById("status");
const statusText = document.getElementById("status-text");

const error = document.getElementById("error");
const errorText = document.getElementById("error-text");

const result = document.getElementById("result");
const resultText = document.getElementById("result-text");
const frameImage = document.getElementById("frame-image");
const resultTimestamp = document.getElementById("result-timestamp");
const resultFrame = document.getElementById("result-frame");

const video = document.getElementById("video-player");

const dialogueRange = document.getElementById("dialogue-range");
const timelinePointer = document.getElementById("timeline-pointer");

const timelineStart = document.getElementById("timeline-start");
const timelineEnd = document.getElementById("timeline-end");


const useOcrInput = document.getElementById("use-ocr");
const resultSource = document.getElementById("result-source");


let dialogueStart = 0;
let dialogueEnd = 0;
let frameTimestamp = 0;


// =========================================================
// Helpers
// =========================================================

function show(element) {
  if (element) {
    element.classList.remove("hidden");
  }
}


function hide(element) {
  if (element) {
    element.classList.add("hidden");
  }
}


function formatTimestamp(seconds) {
  const totalSeconds = Number(seconds);

  if (!Number.isFinite(totalSeconds)) {
    return "--:--.--";
  }

  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${remainingSeconds
    .toFixed(2)
    .padStart(5, "0")}`;
}


function setProcessing(isProcessing) {
  findButton.disabled = isProcessing;

  findButton.textContent = isProcessing
    ? "PROCESSING..."
    : "FIND EXACT FRAME";
}


// =========================================================
// Main request
// =========================================================

async function findExactFrame() {

  const videoUrl = videoUrlInput.value.trim();
  const dialogue = dialogueInput.value.trim();

  hide(error);
  hide(result);

  if (!videoUrl) {
    showError("Please enter a video URL.");
    return;
  }

  if (!dialogue) {
    showError("Please enter the dialogue.");
    return;
  }

  setProcessing(true);

  show(status);
  statusText.textContent = "Analyzing video...";

  try {

    const response = await fetch(
      `${API_URL}/find-dialogue`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify({
          video_url: videoUrl,
          dialogue: dialogue,
          use_ocr: useOcrInput.checked
        })
      }
    );


    // -------------------------------------------------------
    // HTTP error
    // -------------------------------------------------------

    if (!response.ok) {

      let message =
        `Request failed with status ${response.status}.`;

      try {

        const errorData = await response.json();

        if (errorData.detail) {

          message = Array.isArray(errorData.detail)
            ? "Invalid request."
            : errorData.detail;
        }

      } catch {
        // Keep default message.
      }

      throw new Error(message);
    }


    // -------------------------------------------------------
    // Response
    // -------------------------------------------------------

    const data = await response.json();

    hide(status);


    // -------------------------------------------------------
    // Dialogue not found
    // -------------------------------------------------------

    if (!data.success) {

      showError(
        data.message ||
        "Dialogue was not found in the video."
      );

      return;
    }


    // -------------------------------------------------------
    // Display result
    // -------------------------------------------------------

    displayResult(data);

  } catch (err) {

    hide(status);

    if (err instanceof TypeError) {

      showError(
        "Unable to connect to the backend. " +
        "Make sure the FastAPI server is running."
      );

    } else {

      showError(
        err.message ||
        "Something went wrong while processing the video."
      );
    }

  } finally {

    setProcessing(false);
  }
}


// =========================================================
// Display result
// =========================================================

function displayResult(data) {

  // -------------------------------------------------------
  // Dialogue
  // -------------------------------------------------------

  resultText.textContent = data.text;

  dialogueStart = Number(data.start_time);
  dialogueEnd = Number(data.end_time);
  frameTimestamp = Number(data.frame_timestamp);
  // dialogueStart = Number(data.start_time);
  //  dialogueEnd = Number(data.end_time);
  //  frameTimestamp = Number(data.frame_timestamp);
  //


  // -------------------------------------------------------
  // Validate timestamps
  // -------------------------------------------------------

  if (!Number.isFinite(dialogueStart)) {
    dialogueStart = 0;
  }

  if (!Number.isFinite(dialogueEnd)) {
    dialogueEnd = dialogueStart;
  }

  if (!Number.isFinite(frameTimestamp)) {
    frameTimestamp = dialogueStart;
  }
  if (resultSource) {
    resultSource.textContent = data.match_source === "ocr" ? "OCR" : "WHISPER";
  }


  // -------------------------------------------------------
  // Metadata
  // -------------------------------------------------------

  resultTimestamp.textContent =
    `${formatTimestamp(dialogueStart)} → ${formatTimestamp(dialogueEnd)}`;

  resultFrame.textContent =
    data.frame_number;


  // -------------------------------------------------------
  // Extracted frame
  // -------------------------------------------------------

  if (data.frame_url) {

    frameImage.src =
      `${API_URL}${data.frame_url}`;

    frameImage.alt =
      `Frame ${data.frame_number} from the video`;

  } else {

    frameImage.removeAttribute("src");
    frameImage.alt = "No extracted frame available";
  }


  // -------------------------------------------------------
  // Timeline labels
  // -------------------------------------------------------

  if (timelineStart) {

    timelineStart.textContent =
      formatTimestamp(dialogueStart);
  }

  if (timelineEnd) {

    timelineEnd.textContent =
      formatTimestamp(dialogueEnd);
  }


  // -------------------------------------------------------
  // Reset timeline visuals
  // -------------------------------------------------------

  if (dialogueRange) {

    dialogueRange.style.left = "0%";
    dialogueRange.style.width = "0%";
  }

  if (timelinePointer) {

    timelinePointer.style.left = "0%";
  }


  // -------------------------------------------------------
  // Video URL
  // -------------------------------------------------------

  if (!data.video_url) {

    showError(
      "The backend did not return a video URL."
    );

    return;
  }


  // -------------------------------------------------------
  // Load full video
  // -------------------------------------------------------

  video.src =
    `${API_URL}${data.video_url}`;

  video.load();


  // -------------------------------------------------------
  // Calculate timeline after metadata loads
  // -------------------------------------------------------

  video.addEventListener(
    "loadedmetadata",
    updateTimeline,
    { once: true }
  );


  // -------------------------------------------------------
  // Show result
  // -------------------------------------------------------

  show(result);
}


// =========================================================
// Timeline visualization
// =========================================================

function updateTimeline() {

  const duration = video.duration;

  if (
    !Number.isFinite(duration) ||
    duration <= 0
  ) {
    return;
  }


  // -------------------------------------------------------
  // Clamp timestamps to video duration
  // -------------------------------------------------------

  const safeStart =
    Math.min(
      Math.max(dialogueStart, 0),
      duration
    );

  const safeEnd =
    Math.min(
      Math.max(dialogueEnd, safeStart),
      duration
    );

  const safeFrame =
    Math.min(
      Math.max(frameTimestamp, 0),
      duration
    );


  // -------------------------------------------------------
  // Dialogue highlighted range
  // -------------------------------------------------------

  const startPercent =
    (safeStart / duration) * 100;

  const endPercent =
    (safeEnd / duration) * 100;


  if (dialogueRange) {

    dialogueRange.style.left =
      `${startPercent}%`;

    dialogueRange.style.width =
      `${Math.max(0, endPercent - startPercent)}%`;
  }


  // -------------------------------------------------------
  // Exact frame pointer
  // -------------------------------------------------------

  const framePercent =
    (safeFrame / duration) * 100;


  if (timelinePointer) {

    timelinePointer.style.left =
      `${Math.min(
        100,
        Math.max(0, framePercent)
      )}%`;
  }


  // -------------------------------------------------------
  // Start video at detected dialogue
  // -------------------------------------------------------

  video.currentTime = safeStart;
}


// =========================================================
// Update pointer while user watches / seeks
// =========================================================

video.addEventListener(
  "timeupdate",
  () => {

    const duration = video.duration;

    if (
      !Number.isFinite(duration) ||
      duration <= 0
    ) {
      return;
    }


    const currentPercent =
      (video.currentTime / duration) * 100;


    /*
     * The pointer represents the
     * current position in the video.
     *
     * The user can freely play or
     * seek through the entire video.
     */

    if (timelinePointer) {

      timelinePointer.style.left =
        `${Math.min(
          100,
          Math.max(0, currentPercent)
        )}%`;
    }

  }
);


// =========================================================
// Error handling
// =========================================================

function showError(message) {

  errorText.textContent = message;

  show(error);
}


// =========================================================
// Events
// =========================================================

findButton.addEventListener(
  "click",
  findExactFrame
);


dialogueInput.addEventListener(
  "keydown",
  (event) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      findExactFrame();
    }

  }
);
