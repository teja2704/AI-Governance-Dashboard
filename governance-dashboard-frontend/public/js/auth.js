// auth.js — handlers for login.html, signup.html, forgot-password.html

function showError(el, message) {
  el.textContent = message;
  el.classList.remove('hidden');
}

function clearError(el) {
  el.textContent = '';
  el.classList.add('hidden');
}

function guardAuthPage() {
  // If already logged in, skip straight to dashboard
  if (isLoggedIn()) {
    window.location.href = '/dashboard.html';
  }
}

// ---------- LOGIN (two-step: email → password) ----------
function initLoginPage() {
  guardAuthPage();

  // DOM refs for step 1
  const stepEmail    = document.getElementById('step-email');
  const emailForm    = document.getElementById('email-form');
  const loginError   = document.getElementById('login-error');

  // DOM refs for step 2
  const stepPassword = document.getElementById('step-password');
  const passwordForm = document.getElementById('password-form');
  const passwordError = document.getElementById('password-error');
  const emailDisplay = document.getElementById('email-display');
  const backBtn      = document.getElementById('back-btn');

  // Google placeholder
  const googleBtn    = document.getElementById('google-btn');
  const googleNotice = document.getElementById('google-notice');

  let confirmedEmail = '';

  // ---- Step 1: submit email → advance to password step ----
  emailForm.addEventListener('submit', (e) => {
    e.preventDefault();
    clearError(loginError);

    const email = emailForm.email.value.trim();
    if (!email) {
      showError(loginError, 'Please enter your email address.');
      return;
    }

    confirmedEmail = email;
    emailDisplay.textContent = email;
    stepEmail.classList.add('hidden');
    stepPassword.classList.remove('hidden');
    // Auto-focus password field
    document.getElementById('password').focus();
  });

  // ---- Back button: return to email step ----
  backBtn.addEventListener('click', () => {
    stepPassword.classList.add('hidden');
    stepEmail.classList.remove('hidden');
    clearError(passwordError);
    document.getElementById('email').focus();
  });

  // ---- Step 2: submit password → POST /auth/login ----
  passwordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError(passwordError);

    const password = passwordForm.password.value;
    if (!password) {
      showError(passwordError, 'Please enter your password.');
      return;
    }

    const submitBtn = passwordForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in…';

    try {
      // Payload confirmed from backend LoginRequest schema: { email, password }
      const data = await api.post('/auth/login', { email: confirmedEmail, password }, { auth: false });
      setToken(data.access_token);
      window.location.href = '/dashboard.html';
    } catch (err) {
      if (err.status === 429) {
        showError(passwordError, 'Too many login attempts. Please wait a minute and try again.');
      } else if (err.status === 401) {
        showError(passwordError, 'Invalid email or password.');
      } else {
        showError(passwordError, err.message || 'Login failed.');
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  });

  // ---- Google placeholder ----
  googleBtn.addEventListener('click', () => {
    googleNotice.classList.add('visible');
  });
}

// ---------- SIGNUP ----------
function initSignupPage() {
  guardAuthPage();
  const form     = document.getElementById('signup-form');
  const errorEl  = document.getElementById('signup-error');
  const googleBtn    = document.getElementById('google-btn');
  const googleNotice = document.getElementById('google-notice');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError(errorEl);

    // Payload confirmed from backend SignupRequest schema:
    // { first_name, last_name, email, password }
    const first_name = form.first_name.value.trim();
    const last_name  = form.last_name.value.trim();
    const email      = form.email.value.trim();
    const password   = form.password.value;

    if (!first_name || !last_name || !email || !password) {
      showError(errorEl, 'All fields are required.');
      return;
    }
    if (password.length < 8) {
      showError(errorEl, 'Password must be at least 8 characters.');
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account…';

    try {
      const data = await api.post(
        '/auth/signup',
        { first_name, last_name, email, password },
        { auth: false }
      );
      // Backend returns access_token on successful signup — auto-login
      if (data.access_token) {
        setToken(data.access_token);
        window.location.href = '/dashboard.html';
      } else {
        window.location.href = '/login.html';
      }
    } catch (err) {
      if (err.status === 409) {
        showError(errorEl, 'An account with that email already exists.');
      } else if (err.status === 422) {
        showError(errorEl, 'Password must be at least 8 characters.');
      } else {
        showError(errorEl, err.message || 'Signup failed. Please try again.');
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Account';
    }
  });

  // ---- Google placeholder ----
  googleBtn.addEventListener('click', () => {
    googleNotice.classList.add('visible');
  });
}

// ---------- FORGOT PASSWORD (3-step: request → verify → reset) ----------
function initForgotPasswordPage() {
  guardAuthPage();

  const steps = {
    request: document.getElementById('step-request'),
    verify:  document.getElementById('step-verify'),
    reset:   document.getElementById('step-reset'),
    done:    document.getElementById('step-done'),
  };

  function showStep(name) {
    Object.values(steps).forEach((el) => el.classList.add('hidden'));
    steps[name].classList.remove('hidden');
  }

  let currentEmail = '';
  let resetToken   = '';

  // Step 1: request OTP — payload: { email }
  const requestForm  = document.getElementById('request-form');
  const requestError = document.getElementById('request-error');
  requestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError(requestError);
    currentEmail = requestForm.email.value.trim();

    if (!currentEmail) {
      showError(requestError, 'Please enter your email address.');
      return;
    }

    const btn = requestForm.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Sending…';

    try {
      // Always returns 200 (anti-enumeration) — just advance to verify step
      await api.post('/auth/forgot-password', { email: currentEmail }, { auth: false });
      showStep('verify');
    } catch (err) {
      showError(requestError, err.message || 'Something went wrong. Please try again.');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Send Code';
    }
  });

  // Step 2: verify OTP — payload: { email, otp }
  const verifyForm  = document.getElementById('verify-form');
  const verifyError = document.getElementById('verify-error');
  verifyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError(verifyError);
    const otp = verifyForm.otp.value.trim();

    const btn = verifyForm.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Verifying…';

    try {
      // Response: { reset_token }
      const data = await api.post('/auth/verify-otp', { email: currentEmail, otp }, { auth: false });
      resetToken = data.reset_token;
      showStep('reset');
    } catch (err) {
      showError(verifyError, err.message || 'Invalid or expired code.');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Verify Code';
    }
  });

  // Step 3: set new password — payload: { reset_token, new_password }
  const resetForm  = document.getElementById('reset-form');
  const resetError = document.getElementById('reset-error');
  resetForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError(resetError);
    const newPassword = resetForm.new_password.value;

    if (newPassword.length < 8) {
      showError(resetError, 'Password must be at least 8 characters.');
      return;
    }

    const btn = resetForm.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Resetting…';

    try {
      await api.post('/auth/reset-password', { reset_token: resetToken, new_password: newPassword }, { auth: false });
      showStep('done');
    } catch (err) {
      showError(resetError, err.message || 'Could not reset password. The link may have expired.');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Reset Password';
    }
  });

  showStep('request');
}

// ---------- LOGOUT (used on dashboard/generate/history pages) ----------
function initLogoutButton() {
  const btn = document.getElementById('logout-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    clearToken();
    window.location.href = '/login.html';
  });
}

// ---------- Protect dashboard/generate/history pages ----------
function guardProtectedPage() {
  if (!isLoggedIn()) {
    window.location.href = '/login.html';
  }
}
