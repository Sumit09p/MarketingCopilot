import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { isMockApiEnabled } from "../services";
import { getUserFacingError } from "../utils/errors";
import { useTheme } from "../context/ThemeContext";

function AuthThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const nextTheme = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      className="auth-theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${nextTheme} theme`}
      aria-pressed={theme === "dark"}
      title={`Switch to ${nextTheme} theme`}
    >
      <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
      <span>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}

function PasswordIcon({ visible }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {visible ? (
        <>
          <path d="M3 3l18 18" />
          <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
          <path d="M9.9 5.2A11.4 11.4 0 0 1 12 5c5 0 8.5 4.2 9.5 6.1a1.8 1.8 0 0 1 0 1.8 14 14 0 0 1-3.1 3.7" />
          <path d="M6.2 6.2A14.3 14.3 0 0 0 2.5 11a1.8 1.8 0 0 0 0 2c1.1 1.9 4.5 6 9.5 6a10 10 0 0 0 3-.5" />
        </>
      ) : (
        <>
          <path d="M2.5 12s3.4-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.4 6.5-9.5 6.5S2.5 12 2.5 12Z" />
          <circle cx="12" cy="12" r="2.6" />
        </>
      )}
    </svg>
  );
}

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const { theme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const registered = Boolean(location.state?.registered);

  if (loading) {
    return (
      <div className="auth-layout">
        <AuthThemeToggle />
        <p className="muted">Restoring session...</p>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/chat" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      setError("Enter your email and password.");
      return;
    }
    if (!trimmedEmail.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      await login({ email: trimmedEmail, password });
      setPassword("");
      navigate("/chat", { replace: true });
    } catch (err) {
      setPassword("");
      setError(
        err?.status === 401
          ? err.message || "Invalid email or password"
          : getUserFacingError(err, "Could not sign in. Please try again.")
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-layout">
      <AuthThemeToggle />
      <form className="auth-card" onSubmit={handleSubmit}>
        <img className="auth-logo" src={theme === "dark" ? "/brand/prism-logo-dark.png" : "/brand/prism-logo.png"} alt="PRISM" />
        <img className="auth-icon" src="/brand/prism-icon.png" alt="PRISM" />
        <h1>Log in</h1>
        <p>Sign in to continue to PRISM</p>
        {registered ? <p className="success-text">Account created. Please sign in.</p> : null}
        {error ? <p className="error-text auth-error" role="alert">{error}</p> : null}
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="password">Password</label>
          <div className="password-input-wrap">
            <input
              id="password"
              type={passwordVisible ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setPasswordVisible((visible) => !visible)}
              aria-label={passwordVisible ? "Hide password" : "Show password"}
              title={passwordVisible ? "Hide password" : "Show password"}
            >
              <PasswordIcon visible={passwordVisible} />
            </button>
          </div>
        </div>
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
        {isMockApiEnabled ? (
          <p className="muted" style={{ marginTop: 16 }}>
            Demo account: john@example.com / password
          </p>
        ) : (
          <p className="muted" style={{ marginTop: 16 }}>
            Use your workspace account to sign in.
          </p>
        )}
        <p className="muted">
          Need an account? <Link className="auth-link" to="/register">Register</Link>
        </p>
      </form>
    </div>
  );
}
