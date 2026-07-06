import React from "react";
import { Outlet, Link, useNavigate } from "react-router-dom";
import { ShoppingBag, User, LogOut, LayoutDashboard, Menu } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useCart } from "@/context/CartContext";
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
  DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

export default function StorefrontLayout() {
  const { user, logout } = useAuth();
  const { count } = useCart();
  const navigate = useNavigate();

  const isAdmin = user && (user.role === "admin" || user.role === "staff");

  return (
    <div className="min-h-screen bg-[#F9F8F6] flex flex-col">
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[#F9F8F6]/85 border-b border-[#E5E1D8]">
        <div className="mx-auto max-w-7xl px-6 lg:px-10 py-5 flex items-center justify-between">
          <Link to="/" data-testid="brand-home-link" className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-[#4A5D23] grid place-items-center">
              <span className="font-serif-display text-[#F9F8F6] text-xl leading-none">K</span>
            </div>
            <div>
              <div className="font-serif-display text-2xl leading-none text-[#1C1C17]">Kaya's</div>
              <div className="font-store text-[10px] tracking-[0.28em] uppercase text-[#5C5C54] mt-0.5">Herbals</div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-10 font-store text-sm text-[#1C1C17]">
            <Link data-testid="nav-shop" to="/shop" className="tick-underline">Shop</Link>
            <Link data-testid="nav-story" to="/#story" className="tick-underline">Our Story</Link>
            <Link data-testid="nav-wholesale" to="/#wholesale" className="tick-underline">Wholesale</Link>
          </nav>

          <div className="flex items-center gap-2">
            <Link to="/cart" data-testid="cart-icon-link" className="relative p-2 hover:bg-[#F2EFE9] rounded-full transition">
              <ShoppingBag className="h-5 w-5 text-[#1C1C17]" strokeWidth={1.5} />
              {count > 0 && (
                <span data-testid="cart-count-badge" className="absolute -top-0.5 -right-0.5 h-5 w-5 rounded-full bg-[#C4654F] text-white text-[10px] font-mono-kh grid place-items-center">
                  {count}
                </span>
              )}
            </Link>
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button data-testid="user-menu-trigger" variant="ghost" size="icon" className="rounded-full">
                    <User className="h-5 w-5" strokeWidth={1.5} />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 font-store">
                  <DropdownMenuLabel className="truncate">{user.name}</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {isAdmin && (
                    <DropdownMenuItem data-testid="menu-admin" onClick={() => navigate("/admin")}>
                      <LayoutDashboard className="h-4 w-4 mr-2" /> Admin dashboard
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem data-testid="menu-my-orders" onClick={() => navigate("/my-orders")}>
                    <ShoppingBag className="h-4 w-4 mr-2" /> My orders
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem data-testid="menu-logout" onClick={logout}>
                    <LogOut className="h-4 w-4 mr-2" /> Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                <Link to="/login" data-testid="nav-login" className="hidden sm:inline-flex items-center h-9 px-4 text-sm font-store hover:bg-[#F2EFE9] rounded-full transition">
                  Login
                </Link>
                <Link to="/register" data-testid="nav-register" className="inline-flex items-center h-9 px-5 text-sm font-store bg-[#1C1C17] text-[#F9F8F6] rounded-full hover:bg-[#4A5D23] transition">
                  Join
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="mt-24 border-t border-[#E5E1D8] bg-[#F2EFE9]">
        <div className="mx-auto max-w-7xl px-6 lg:px-10 py-16 grid grid-cols-1 md:grid-cols-4 gap-10">
          <div>
            <div className="font-serif-display text-3xl text-[#1C1C17]">Kaya's Herbals</div>
            <p className="font-store text-sm text-[#5C5C54] mt-4 leading-relaxed">
              Ancient Ayurvedic wisdom, distilled into modern rituals. Grown, blended and bottled in India.
            </p>
          </div>
          <div>
            <div className="font-dash text-xs tracking-widest uppercase text-[#5C5C54]">Shop</div>
            <ul className="mt-4 space-y-2 font-store text-sm text-[#1C1C17]">
              <li><Link to="/shop">All products</Link></li>
              <li><Link to="/shop?category=Powders">Powders</Link></li>
              <li><Link to="/shop?category=Skincare">Skincare</Link></li>
              <li><Link to="/shop?category=Teas">Teas</Link></li>
            </ul>
          </div>
          <div>
            <div className="font-dash text-xs tracking-widest uppercase text-[#5C5C54]">Business</div>
            <ul className="mt-4 space-y-2 font-store text-sm text-[#1C1C17]">
              <li><Link to="/register">Become a distributor</Link></li>
              <li><Link to="/login">Distributor login</Link></li>
              <li><Link to="/admin">ERP dashboard</Link></li>
            </ul>
          </div>
          <div>
            <div className="font-dash text-xs tracking-widest uppercase text-[#5C5C54]">Contact</div>
            <ul className="mt-4 space-y-2 font-store text-sm text-[#1C1C17]">
              <li>hello@kayaherbals.com</li>
              <li>+91 98xxxxxx00</li>
              <li>Bengaluru, India</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-[#E5E1D8] py-6 text-center font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
          © {new Date().getFullYear()} Kaya's Herbals — ERP & Storefront
        </div>
      </footer>
    </div>
  );
}
