import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Link } from "react-router-dom";

const STATUS_COLORS = {
  pending: "bg-[#D4A373] text-white",
  processing: "bg-[#4A5D23] text-white",
  shipped: "bg-[#365E32] text-white",
  delivered: "bg-[#4A5D23] text-white",
  cancelled: "bg-[#A43026] text-white",
};

export default function MyOrders() {
  const [orders, setOrders] = useState([]);
  useEffect(() => {
    api.get("/orders").then(({ data }) => setOrders(data)).catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-6 py-14">
      <h1 className="font-serif-display text-5xl">My orders</h1>
      {orders.length === 0 ? (
        <div className="mt-12 py-24 text-center font-store text-[#5C5C54]">No orders yet.</div>
      ) : (
        <div className="mt-10 space-y-4">
          {orders.map((o) => (
            <Link
              key={o.id}
              to={`/order/${o.id}`}
              data-testid={`my-order-${o.order_number}`}
              className="block p-5 rounded-lg border border-[#E5E1D8] bg-white hover:border-[#4A5D23] transition"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-mono-kh text-xs uppercase tracking-widest text-[#5C5C54]">{o.order_number}</div>
                  <div className="mt-1 font-dash font-bold">{o.items.length} items · ₹{o.grand_total.toFixed(2)}</div>
                  <div className="mt-1 font-store text-xs text-[#5C5C54]">{new Date(o.created_at).toLocaleString()}</div>
                </div>
                <span className={`px-3 py-1 rounded-full font-mono-kh text-[10px] tracking-widest uppercase ${STATUS_COLORS[o.status] || ""}`}>
                  {o.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
