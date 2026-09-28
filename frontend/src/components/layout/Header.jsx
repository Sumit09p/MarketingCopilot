import { useAuth } from "../../hooks/useAuth";
import { isMockApiEnabled } from "../../services";

export default function Header({ title }) {
  const { user, logout } = useAuth();

  return (
    <header className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-meta">
        {isMockApiEnabled ? <span className="badge">Mock API</span> : <span className="badge">Live API</span>}
        <span>{user?.name ?? "Guest"}</span>
        <button type="button" className="btn btn-secondary" onClick={logout}>
          Log out
        </button>
      </div>
    </header>
  );
}
