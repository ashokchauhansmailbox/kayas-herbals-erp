import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Package, ShoppingCart, Users, TrendingUp, AlertTriangle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";

const StatCard = ({ icon: Icon, label, value, sub, accent }) => (
  <div className="p-5 bg-white border border-[#E5E1D8] rounded-lg">
    <div className="flex items-center justify-between">
      <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">{label}</div>
      <Icon className="h-4 w-4" style={{ color: accent || "#4A5D23" }} strokeWidth={1.5} />
    </div>
    <div className="mt-3 font-dash font-bold text-3xl">{value}</div>
    {sub && <div className="mt-1 font-mono-kh text-[10px] text-[#5C5C54] uppercase tracking-widest">{sub}</div>}
  </div>
);

export default function DashboardHome() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/reports/dashboard").then(({ data }) => setD(data)).catch(() => {}); }, []);

  if (!d) return <div className="font-store text-[#5C5C54]">Loading…</div>;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-6">
        <div>
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Control room</div>
          <h1 className="font-dash font-bold text-3xl mt-1">Overview</h1>
        </div>
        <div className="font-mono-kh text-xs text-[#5C5C54]">{new Date().toLocaleString()}</div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4" data-testid="dashboard-stats">
        <StatCard icon={TrendingUp} label="Revenue" value={`₹${d.revenue.toLocaleString()}`} sub="lifetime" accent="#C4654F" />
        <StatCard icon={ShoppingCart} label="Orders" value={d.total_orders} sub={`${d.pending_orders} pending`} />
        <StatCard icon={Package} label="Products" value={d.total_products} sub={`${d.active_products} active`} />
        <StatCard icon={Users} label="Distributors" value={d.total_distributors} sub="in network" />
        <StatCard icon={AlertTriangle} label="Low stock" value={d.low_stock.length} sub="items to reorder" accent="#A43026" />
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 p-5 bg-white border border-[#E5E1D8] rounded-lg">
          <div className="flex items-center justify-between">
            <div className="font-dash font-bold">Revenue — last 7 days</div>
            <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">₹ · daily</div>
          </div>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={d.daily_sales}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E1D8" />
                <XAxis dataKey="date" stroke="#5C5C54" fontSize={11} />
                <YAxis stroke="#5C5C54" fontSize={11} />
                <Tooltip contentStyle={{ background: "#F9F8F6", border: "1px solid #E5E1D8" }} />
                <Line type="monotone" dataKey="revenue" stroke="#4A5D23" strokeWidth={2} dot={{ r: 3, fill: "#C4654F" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-5 bg-white border border-[#E5E1D8] rounded-lg">
          <div className="font-dash font-bold">Top products</div>
          <div className="mt-4 space-y-3" data-testid="top-products">
            {d.top_products.length === 0 && <div className="font-store text-sm text-[#5C5C54]">No sales yet.</div>}
            {d.top_products.map((t, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="min-w-0">
                  <div className="font-store text-sm truncate">{t.name}</div>
                  <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">{t.qty} sold</div>
                </div>
                <div className="font-mono-kh text-sm">₹{t.sales.toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 p-5 bg-white border border-[#E5E1D8] rounded-lg">
        <div className="flex items-center justify-between">
          <div className="font-dash font-bold">Low stock alerts</div>
          <span className="font-mono-kh text-[10px] tracking-widest uppercase text-[#A43026]">reorder soon</span>
        </div>
        {d.low_stock.length === 0 ? (
          <div className="mt-3 font-store text-sm text-[#5C5C54]">All products above threshold.</div>
        ) : (
          <table className="w-full mt-4 text-sm">
            <thead className="text-left font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
              <tr><th className="py-2">SKU</th><th>Name</th><th className="text-right">Stock</th><th className="text-right">Threshold</th></tr>
            </thead>
            <tbody className="font-store">
              {d.low_stock.map((p) => (
                <tr key={p.id} className="border-t border-[#E5E1D8]">
                  <td className="py-2 font-mono-kh text-xs">{p.sku}</td>
                  <td>{p.name}</td>
                  <td className="text-right font-mono-kh text-[#A43026] font-bold">{p.stock}</td>
                  <td className="text-right font-mono-kh text-[#5C5C54]">{p.low_stock_threshold}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
