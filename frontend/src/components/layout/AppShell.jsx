import { Outlet, useLocation } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";

const titles = {
  "/chat": "Chat",
  "/dashboard": "Dashboard",
  "/brand": "Brand profile",
  "/campaigns": "Campaigns",
  "/campaigns/new": "New campaign",
  "/calendar": "Calendar",
  "/knowledge": "Knowledge",
  "/integrations": "Integrations",
};

export default function AppShell() {
  const { pathname } = useLocation();
  const title = titles[pathname] ?? "MarketingOS AI";

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="shell-main">
        <Header title={title} />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
