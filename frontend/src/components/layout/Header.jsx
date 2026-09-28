import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { isMockApiEnabled } from "../../services";

export default function Header({ title }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-meta">
        {isMockApiEnabled ? <span className="badge">Mock API</span> : <span className="badge">Live API</span>}
        <div className="header-user">
          <span className="header-user-name">{user?.name ?? "Guest"}</span>
          {user?.email ? <span className="header-user-email">{user.email}</span> : null}
        </div>
        <button type="button" className="btn btn-secondary" onClick={handleLogout} aria-label="Log out">
          Log out
        </button>
      </div>
    </header>
  );
}
