import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/common/PageHeader";
import { useAuth } from "../hooks/useAuth";
import { authService, isMockApiEnabled } from "../services";
import { getUserFacingError } from "../utils/errors";

const MIN_PASSWORD_LENGTH = 6;

function PasswordField({ id, label, value, onChange, visible, onToggle, autoComplete }) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className="password-input-wrap">
        <input
          id={id}
          type={visible ? "text" : "password"}
          autoComplete={autoComplete}
          value={value}
          onChange={onChange}
          required
        />
        <button
          type="button"
          className="password-toggle"
          onClick={onToggle}
          aria-label={`${visible ? "Hide" : "Show"} ${label.toLowerCase()}`}
          aria-pressed={visible}
          title={`${visible ? "Hide" : "Show"} ${label.toLowerCase()}`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            {visible ? <><path d="M3 3l18 18" /><path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" /><path d="M9.9 5.2A11.4 11.4 0 0 1 12 5c5 0 8.5 4.2 9.5 6.1a1.8 1.8 0 0 1 0 1.8 14 14 0 0 1-3.1 3.7" /><path d="M6.2 6.2A14.3 14.3 0 0 0 2.5 11a1.8 1.8 0 0 0 0 2c1.1 1.9 4.5 6 9.5 6a10 10 0 0 0 3-.5" /></> : <><path d="M2.5 12s3.4-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.4 6.5-9.5 6.5S2.5 12 2.5 12Z" /><circle cx="12" cy="12" r="2.6" /></>}
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [passwords, setPasswords] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });
  const [visibility, setVisibility] = useState({ currentPassword: false, newPassword: false, confirmPassword: false });
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  function updatePassword(field, value) {
    setPasswords((current) => ({ ...current, [field]: value }));
    setPasswordError("");
    setPasswordSuccess("");
  }

  async function handleChangePassword(event) {
    event.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    if (!passwords.currentPassword || !passwords.newPassword || !passwords.confirmPassword) {
      setPasswordError("Enter your current password and complete both new password fields.");
      return;
    }
    if (passwords.newPassword.length < MIN_PASSWORD_LENGTH) {
      setPasswordError(`New password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (passwords.newPassword !== passwords.confirmPassword) {
      setPasswordError("New password and confirmation do not match.");
      return;
    }
    if (passwords.currentPassword === passwords.newPassword) {
      setPasswordError("Choose a new password that differs from your current password.");
      return;
    }

    setChangingPassword(true);
    try {
      await authService.changePassword({ currentPassword: passwords.currentPassword, newPassword: passwords.newPassword });
      setPasswords({ currentPassword: "", newPassword: "", confirmPassword: "" });
      setPasswordSuccess(isMockApiEnabled ? "Password changed in demo mode for this session." : "Password changed successfully.");
    } catch (error) {
      setPasswordError(getUserFacingError(error, "Could not change your password. Please try again."));
    } finally {
      setChangingPassword(false);
    }
  }

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      navigate("/login", { replace: true });
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <section className="page-stack profile-page">
      <PageHeader title="Profile" description="Your PRISM account information and access settings." />
      <section className="page-card">
        <h2>Account information</h2>
        <dl className="meta-list profile-details">
          <dt>Name</dt><dd>{user?.name || "-"}</dd>
          <dt>Email</dt><dd>{user?.email || "-"}</dd>
        </dl>
      </section>
      <section className="page-card">
        <h2>Change password</h2>
        <p className="muted">Use at least {MIN_PASSWORD_LENGTH} characters for your new password.</p>
        <form className="stack-form profile-password-form" onSubmit={handleChangePassword}>
          <PasswordField id="current-password" label="Current password" autoComplete="current-password" value={passwords.currentPassword} onChange={(event) => updatePassword("currentPassword", event.target.value)} visible={visibility.currentPassword} onToggle={() => setVisibility((current) => ({ ...current, currentPassword: !current.currentPassword }))} />
          <PasswordField id="new-password" label="New password" autoComplete="new-password" value={passwords.newPassword} onChange={(event) => updatePassword("newPassword", event.target.value)} visible={visibility.newPassword} onToggle={() => setVisibility((current) => ({ ...current, newPassword: !current.newPassword }))} />
          <PasswordField id="confirm-new-password" label="Confirm new password" autoComplete="new-password" value={passwords.confirmPassword} onChange={(event) => updatePassword("confirmPassword", event.target.value)} visible={visibility.confirmPassword} onToggle={() => setVisibility((current) => ({ ...current, confirmPassword: !current.confirmPassword }))} />
          {passwordError ? <p className="error-text" role="alert">{passwordError}</p> : null}
          {passwordSuccess ? <p className="success-text" role="status">{passwordSuccess}</p> : null}
          <button type="submit" className="btn" disabled={changingPassword}>{changingPassword ? "Changing password..." : "Change password"}</button>
        </form>
      </section>
      <section className="page-card profile-logout-card">
        <div>
          <h2>Sign out</h2>
          <p>End your current PRISM session on this device.</p>
        </div>
        <button type="button" className="btn btn-danger profile-logout" onClick={handleLogout} disabled={loggingOut}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M10 17l5-5-5-5M15 12H3" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /></svg>
          {loggingOut ? "Signing out..." : "Log out"}
        </button>
      </section>
    </section>
  );
}
