import { Outlet, useLocation } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";

const titles = {
  "/chat": "Chat",
  "/dashboard": "Dashboard",
  "/analytics": "Analytics",
  "/brand": "Brand profile",
  "/campaigns": "Campaigns",
  "/campaigns/new": "New campaign",
  "/calendar": "Calendar",
  "/knowledge": "Knowledge Base",
  "/integrations": "Integrations",
};

function titleFromPath(pathname) {
  if (titles[pathname]) return titles[pathname];
  if (pathname.startsWith("/campaigns/")) return "Campaign workspace";
  return "MarketingOS AI";
}

export default function AppShell() {
  const { pathname } = useLocation();
  const title = titleFromPath(pathname);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="shell-main">
        <Header title={title} />
        <main className={pathname === "/chat" ? "content content-chat" : "content"}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
