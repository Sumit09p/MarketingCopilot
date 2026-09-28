import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getUserFacingError } from "../utils/errors";

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const registered = Boolean(location.state?.registered);

  if (loading) {
    return (
      <div className="auth-layout">
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
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Log in</h1>
        <p>Sign in to continue to MarketingOS AI.</p>
        {registered ? <p className="success-text">Account created. Please sign in.</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
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
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
        <p className="muted" style={{ marginTop: 16 }}>
          Demo account: john@example.com / password
        </p>
        <p className="muted">
          Need an account? <Link to="/register">Register</Link>
        </p>
      </form>
    </div>
  );
}
