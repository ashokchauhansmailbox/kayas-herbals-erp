import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "@/lib/api";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function OrderConfirmation() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  useEffect(() => {
    api.get(`/orders/${id}`).then(({ data }) => setOrder(data)).catch(() => setOrder(false));
  }, [id]);

  if (order === null) return <div className="py-32 text-center font-store text-[#5C5C54]">Loading…</div>;
  if (!order) return <div className="py-32 text-center font-store text-[#5C5C54]">Order not found.</div>;

  return (
    <div className="mx-auto max-w-3xl px-6 py-20 text-center">
      <CheckCircle2 className="h-16 w-16 mx-auto text-[#4A5D23]" strokeWidth={1.2} />
      <h1 className="mt-6 font-serif-display text-5xl">Thank you</h1>
      <p className="mt-3 font-store text-[#5C5C54]">Your order has been placed successfully.</p>
      <div data-testid="order-number" className="mt-8 inline-block px-6 py-3 rounded-full border border-[#E5E1D8] font-mono-kh text-sm">
        {order.order_number}
      </div>
      <div className="mt-10 text-left rounded-lg border border-[#E5E1D8] bg-white p-6">
        <div className="font-dash font-bold">Order details</div>
        <div className="mt-4 space-y-2">
          {order.items.map((i, idx) => (
            <div key={idx} className="flex justify-between font-store text-sm">
              <span>{i.name} × {i.quantity}</span>
              <span className="font-mono-kh">₹{i.line_total.toFixed(2)}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 border-t border-[#E5E1D8] pt-4 font-store text-sm space-y-1">
          <div className="flex justify-between"><span>Subtotal</span><span className="font-mono-kh">₹{order.subtotal.toFixed(2)}</span></div>
          <div className="flex justify-between"><span>GST</span><span className="font-mono-kh">₹{order.gst_total.toFixed(2)}</span></div>
          <div className="flex justify-between font-dash font-bold text-lg pt-2 border-t border-[#E5E1D8] mt-2"><span>Total</span><span className="font-mono-kh">₹{order.grand_total.toFixed(2)}</span></div>
        </div>
      </div>
      <Button asChild className="mt-8 rounded-full h-11 px-6 bg-[#4A5D23] hover:bg-[#3D4D1D]"><Link to="/shop">Continue shopping</Link></Button>
    </div>
  );
}
