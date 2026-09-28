import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/chat" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register({ name, email, password });
      setPassword("");
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-layout">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Register</h1>
        <p>Creates a mock user session account. Passwords are not stored.</p>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="form-field">
          <label htmlFor="name">Name</label>
          <input id="name" value={name} onChange={(event) => setName(event.target.value)} required />
        </div>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>
        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
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
