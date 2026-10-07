import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { isMockApiEnabled } from "../../services";
import { useTheme } from "../../context/ThemeContext";

export default function Header({ title }) {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-meta">
        {isMockApiEnabled ? <span className="badge">Mock API</span> : <span className="badge">Live API</span>}
        <button type="button" className="theme-toggle" onClick={toggleTheme} aria-pressed={theme === "dark"} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>
          <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
          <span className="theme-toggle-label">{theme === "dark" ? "Light" : "Dark"}</span>
        </button>
        <Link to="/profile" className="header-user" aria-label={`View profile for ${user?.name ?? "Guest"}`}>
          <span className="header-user-name">{user?.name ?? "Guest"}</span>
          {user?.email ? <span className="header-user-email">{user.email}</span> : null}
        </Link>
      </div>
    </header>
  );
}
