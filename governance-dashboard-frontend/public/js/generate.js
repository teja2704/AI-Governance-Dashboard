// generate.js — AI response generation page logic.
// Depends on: api.js (api, ApiError), auth.js (guardProtectedPage, initLogoutButton)
//
// Endpoint: POST /prompts/generate  body: { prompt }
// Success:  HTTP 200  →  { prompt, response, prompt_id, response_id }
// Failure:  HTTP 502  →  ApiError thrown by api.js with detail.message extracted
//
// The api.js wrapper already: attaches JWT, enforces 15 s timeout,
// throws ApiError on non-2xx or abort.  No duplicate mechanism needed.

guardProtectedPage();
initLogoutButton();

// ── DOM refs ──────────────────────────────────────────────────────────────────
const form         = document.getElementById('generate-form');
const promptInput  = document.getElementById('prompt-input');
const submitBtn    = document.getElementById('generate-btn');
const errorEl      = document.getElementById('generate-error');
const successEl    = document.getElementById('generate-success');
const responseWrap = document.getElementById('response-section');
const responseBox  = document.getElementById('response-box');

// ── Helpers ───────────────────────────────────────────────────────────────────
function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
  successEl.classList.add('hidden');
  responseWrap.classList.add('hidden');
}

function clearFeedback() {
  errorEl.classList.add('hidden');
  successEl.classList.add('hidden');
}

function setLoading(isLoading) {
  submitBtn.disabled      = isLoading;
  promptInput.disabled    = isLoading;
  submitBtn.textContent   = isLoading ? 'Generating…' : 'Generate';
}

// ── Form submit handler ───────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearFeedback();

  const prompt = promptInput.value.trim();
  if (!prompt) {
    showError('Please enter a prompt before submitting.');
    return;
  }

  setLoading(true);
  responseWrap.classList.add('hidden');

  try {
    // api.post uses the same 15 s timeout + AbortController as all other requests.
    // On HTTP 502 the backend returns { detail: { message, prompt_id, response_id } }.
    // api.js extracts detail (string or object) into ApiError.message.
    const data = await api.post('/prompts/generate', { prompt });

    // HTTP 200: data.response is the AI-generated text.
    // Guard against a theoretically empty response body just in case.
    if (!data || !data.response) {
      showError('The server returned an empty response. Please try again.');
      return;
    }

    responseBox.textContent = data.response;
    responseWrap.classList.remove('hidden');
    successEl.textContent = 'Response generated successfully.';
    successEl.classList.remove('hidden');

  } catch (err) {
    // ApiError covers: network failure, timeout (AbortError), HTTP 502, HTTP 4xx
    showError(err.message || 'AI generation failed. Please try again shortly.');
  } finally {
    setLoading(false);
  }
});
