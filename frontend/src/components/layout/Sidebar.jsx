import { NavLink } from "react-router-dom";
import { useTheme } from "../../context/ThemeContext";

const links = [
  { to: "/chat", label: "Chat" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analytics", label: "Analytics" },
  { to: "/brand", label: "Brand" },
  { to: "/campaigns", label: "Campaigns" },
  { to: "/calendar", label: "Calendar" },
  { to: "/knowledge", label: "Knowledge" },
  { to: "/integrations", label: "Integrations" },
];

function isPrefixNav(to) {
  return to === "/campaigns";
}

export default function Sidebar() {
  const { theme } = useTheme();
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <img className="sidebar-logo" src={theme === "dark" ? "/brand/prism-logo-right-dark.png" : "/brand/prism-logo-right.png"} alt="PRISM" />
        <img className="sidebar-icon" src="/brand/prism-icon.png" alt="PRISM" />
        <span>AI Marketing Copilot</span>
      </div>
      <nav className="sidebar-nav" aria-label="Main">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={!isPrefixNav(link.to)}
            className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
