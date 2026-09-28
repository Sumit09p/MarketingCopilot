import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getUserFacingError } from "../utils/errors";

export default function RegisterPage() {
  const { user, loading, register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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
    const trimmedName = name.trim();
    const trimmedEmail = email.trim();

    if (!trimmedName || !trimmedEmail || !password) {
      setError("Name, email, and password are required.");
      return;
    }
    if (!trimmedEmail.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      await register({ name: trimmedName, email: trimmedEmail, password });
      setPassword("");
      setConfirmPassword("");
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (err) {
      setPassword("");
      setConfirmPassword("");
      setError(getUserFacingError(err, "Could not create your account. Please try again."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-layout">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Register</h1>
        <p>Create an account, then sign in. Registration does not return a session token.</p>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="form-field">
          <label htmlFor="name">Name</label>
          <input
            id="name"
            autoComplete="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </div>
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
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="confirm-password">Confirm password</label>
          <input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
        </div>
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "Creating account..." : "Create account"}
        </button>
        <p className="muted" style={{ marginTop: 16 }}>
          Already registered? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
