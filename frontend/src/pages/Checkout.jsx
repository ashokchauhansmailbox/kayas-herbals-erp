import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function Checkout() {
  const { items, subtotal, clear } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    customer_name: user?.name || "",
    customer_email: user?.email || "",
    customer_phone: "",
    shipping_address: "",
    notes: "",
  });

  const gst = items.reduce((s, i) => s + i.price * i.quantity * (i.gst_rate / 100), 0);
  const total = subtotal + gst;

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-32 text-center">
        <h1 className="font-serif-display text-4xl">Nothing to checkout</h1>
        <Button asChild className="mt-6 rounded-full h-11 px-6 bg-[#4A5D23] hover:bg-[#3D4D1D]"><Link to="/shop">Shop now</Link></Button>
      </div>
    );
  }

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post("/orders", {
        ...form,
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        order_type: "retail",
        payment_method: "cod",
      });
      clear();
      toast.success("Order placed!");
      navigate(`/order/${data.id}`);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-6 lg:px-10 py-14">
      <h1 className="font-serif-display text-5xl">Checkout</h1>
      <form onSubmit={submit} className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-lg border border-[#E5E1D8] p-6 bg-white">
            <div className="font-dash font-bold">Shipping details</div>
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Full name</Label>
                <Input data-testid="checkout-name" required value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label>Email</Label>
                <Input data-testid="checkout-email" type="email" required value={form.customer_email} onChange={(e) => setForm({ ...form, customer_email: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label>Phone</Label>
                <Input data-testid="checkout-phone" required value={form.customer_phone} onChange={(e) => setForm({ ...form, customer_phone: e.target.value })} className="mt-1" />
              </div>
              <div className="sm:col-span-2">
                <Label>Shipping address</Label>
                <Textarea data-testid="checkout-address" required value={form.shipping_address} onChange={(e) => setForm({ ...form, shipping_address: e.target.value })} className="mt-1" rows={3} />
              </div>
              <div className="sm:col-span-2">
                <Label>Order notes (optional)</Label>
                <Textarea data-testid="checkout-notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="mt-1" rows={2} />
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-[#E5E1D8] p-6 bg-white">
            <div className="font-dash font-bold">Payment</div>
            <div className="mt-4 flex items-center gap-3 p-4 border rounded-md border-[#E5E1D8] bg-[#F9F8F6]">
              <div className="h-4 w-4 rounded-full bg-[#4A5D23]" />
              <div>
                <div className="font-store font-medium">Cash on delivery</div>
                <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Pay when your parcel arrives</div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="rounded-lg border border-[#E5E1D8] p-6 bg-white sticky top-24">
            <div className="font-dash text-sm text-[#5C5C54]">Summary</div>
            <div className="mt-4 space-y-2 max-h-56 overflow-auto">
              {items.map((i) => (
                <div key={i.product_id} className="flex justify-between font-store text-sm">
                  <span className="truncate pr-2">{i.name} × {i.quantity}</span>
                  <span className="font-mono-kh">₹{(i.price * i.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 border-t border-[#E5E1D8] pt-4 space-y-2 font-store text-sm">
              <div className="flex justify-between"><span>Subtotal</span><span className="font-mono-kh">₹{subtotal.toFixed(2)}</span></div>
              <div className="flex justify-between"><span>GST</span><span className="font-mono-kh">₹{gst.toFixed(2)}</span></div>
              <div className="flex justify-between text-lg font-dash font-bold pt-2 border-t border-[#E5E1D8] mt-2"><span>Total</span><span className="font-mono-kh">₹{total.toFixed(2)}</span></div>
            </div>
            <Button data-testid="place-order-btn" type="submit" disabled={busy} className="mt-6 w-full rounded-full h-12 bg-[#4A5D23] hover:bg-[#3D4D1D]">
              {busy ? "Placing order…" : "Place order"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
