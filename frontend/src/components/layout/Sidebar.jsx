import { NavLink } from "react-router-dom";

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

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        MarketingOS AI
        <span>Marketing workspace</span>
      </div>
      <nav className="sidebar-nav" aria-label="Main">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
