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


// ---------------------------------------------------------
// Helpers
// ---------------------------------------------------------

function show(element) {
  element.classList.remove("hidden");
}


function hide(element) {
  element.classList.add("hidden");
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

  if (isProcessing) {
    findButton.textContent = "PROCESSING...";
  } else {
    findButton.textContent = "FIND EXACT FRAME";
  }
}


// ---------------------------------------------------------
// Main request
// ---------------------------------------------------------

async function findExactFrame() {
  const videoUrl = videoUrlInput.value.trim();
  const dialogue = dialogueInput.value.trim();

  hide(error);
  hide(result);

  // Basic client-side validation.
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
    const response = await fetch(`${API_URL}/find-dialogue`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        video_url: videoUrl,
        dialogue: dialogue
      })
    });

    if (!response.ok) {
      let message = `Request failed with status ${response.status}.`;

      try {
        const errorData = await response.json();

        if (errorData.detail) {
          message = Array.isArray(errorData.detail)
            ? "Invalid request."
            : errorData.detail;
        }
      } catch {
        // Keep the default error message.
      }

      throw new Error(message);
    }

    const data = await response.json();

    hide(status);

    if (!data.success) {
      showError(
        data.message || "Dialogue was not found in the video."
      );
      return;
    }

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
        err.message || "Something went wrong while processing the video."
      );
    }

  } finally {
    setProcessing(false);
  }
}


// ---------------------------------------------------------
// Display result
// ---------------------------------------------------------

function displayResult(data) {
  resultText.textContent = data.text;

  resultTimestamp.textContent =
    formatTimestamp(data.frame_timestamp);

  resultFrame.textContent =
    data.frame_number;

  frameImage.src =
    `${API_URL}${data.frame_url}`;

  frameImage.alt =
    `Frame ${data.frame_number} from the video`;

  show(result);
}


// ---------------------------------------------------------
// Error handling
// ---------------------------------------------------------

function showError(message) {
  errorText.textContent = message;

  show(error);
}


// ---------------------------------------------------------
// Events
// ---------------------------------------------------------

findButton.addEventListener("click", findExactFrame);


dialogueInput.addEventListener("keydown", (event) => {
  if (
    event.key === "Enter" &&
    !event.shiftKey
  ) {
    event.preventDefault();
    findExactFrame();
  }
});
