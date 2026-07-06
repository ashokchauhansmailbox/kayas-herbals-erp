import React from "react";
import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Package, Boxes, Users, ShoppingCart, ReceiptText, BarChart3, LogOut, ExternalLink,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

const NAV = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/admin/products", label: "Products", icon: Package },
  { to: "/admin/inventory", label: "Inventory", icon: Boxes },
  { to: "/admin/distributors", label: "Distributors", icon: Users },
  { to: "/admin/orders", label: "Orders", icon: ShoppingCart },
  { to: "/admin/invoices", label: "Invoices & GST", icon: ReceiptText },
  { to: "/admin/reports", label: "Reports", icon: BarChart3 },
];

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F2EFE9] flex">
      <aside className="w-64 shrink-0 border-r border-[#E5E1D8] bg-[#F9F8F6] flex flex-col sticky top-0 h-screen">
        <div className="px-6 py-6 border-b border-[#E5E1D8]">
          <Link to="/" className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-[#4A5D23] grid place-items-center">
              <span className="font-serif-display text-[#F9F8F6] text-xl leading-none">K</span>
            </div>
            <div>
              <div className="font-dash font-bold text-[#1C1C17] leading-none">Kaya ERP</div>
              <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54] mt-1">Control room</div>
            </div>
          </Link>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              data-testid={`nav-${n.label.toLowerCase().replace(/[^a-z]+/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md font-dash text-sm transition
                 ${isActive ? "bg-[#4A5D23] text-[#F9F8F6]" : "text-[#1C1C17] hover:bg-[#F2EFE9]"}`
              }
            >
              <n.icon className="h-4 w-4" strokeWidth={1.5} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-3 py-3 border-t border-[#E5E1D8] space-y-2">
          <Button
            data-testid="view-storefront-btn"
            variant="outline"
            className="w-full justify-start rounded-md font-dash text-sm"
            onClick={() => navigate("/")}
          >
            <ExternalLink className="h-4 w-4 mr-2" strokeWidth={1.5} />
            View storefront
          </Button>
          <div className="px-2 py-2 flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-[#C4654F] grid place-items-center font-dash text-sm text-white">
              {user?.name?.[0]?.toUpperCase() || "A"}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-dash text-sm truncate">{user?.name}</div>
              <div className="font-mono-kh text-[10px] uppercase tracking-widest text-[#5C5C54]">{user?.role}</div>
            </div>
            <button data-testid="logout-btn" onClick={logout} className="p-2 hover:bg-[#F2EFE9] rounded-md" title="Logout">
              <LogOut className="h-4 w-4 text-[#1C1C17]" strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
