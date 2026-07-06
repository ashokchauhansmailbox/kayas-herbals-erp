import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { CartProvider } from "@/context/CartContext";

import StorefrontLayout from "@/layouts/StorefrontLayout";
import DashboardLayout from "@/layouts/DashboardLayout";

import Landing from "@/pages/Landing";
import Shop from "@/pages/Shop";
import ProductDetail from "@/pages/ProductDetail";
import Cart from "@/pages/Cart";
import Checkout from "@/pages/Checkout";
import OrderConfirmation from "@/pages/OrderConfirmation";
import Login from "@/pages/Login";
import Register from "@/pages/Register";

import DashboardHome from "@/pages/dashboard/DashboardHome";
import ProductsAdmin from "@/pages/dashboard/ProductsAdmin";
import InventoryAdmin from "@/pages/dashboard/InventoryAdmin";
import DistributorsAdmin from "@/pages/dashboard/DistributorsAdmin";
import OrdersAdmin from "@/pages/dashboard/OrdersAdmin";
import InvoicesAdmin from "@/pages/dashboard/InvoicesAdmin";
import ReportsAdmin from "@/pages/dashboard/ReportsAdmin";
import MyOrders from "@/pages/MyOrders";

function ProtectedRoute({ children, roles }) {
  const { user } = useAuth();
  if (user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-kh-bg">
        <div className="font-dash text-kh-textSoft text-sm">Loading…</div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <CartProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<StorefrontLayout />}>
                <Route path="/" element={<Landing />} />
                <Route path="/shop" element={<Shop />} />
                <Route path="/product/:id" element={<ProductDetail />} />
                <Route path="/cart" element={<Cart />} />
                <Route path="/checkout" element={<Checkout />} />
                <Route path="/order/:id" element={<OrderConfirmation />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/my-orders" element={<ProtectedRoute><MyOrders /></ProtectedRoute>} />
              </Route>

              <Route
                path="/admin"
                element={
                  <ProtectedRoute roles={["admin", "staff"]}>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardHome />} />
                <Route path="products" element={<ProductsAdmin />} />
                <Route path="inventory" element={<InventoryAdmin />} />
                <Route path="distributors" element={<DistributorsAdmin />} />
                <Route path="orders" element={<OrdersAdmin />} />
                <Route path="invoices" element={<InvoicesAdmin />} />
                <Route path="reports" element={<ReportsAdmin />} />
              </Route>
            </Routes>
            <Toaster richColors position="top-right" />
          </BrowserRouter>
        </CartProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
