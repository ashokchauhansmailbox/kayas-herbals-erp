import React from "react";
import { Link } from "react-router-dom";
import { useCart } from "@/context/CartContext";
import { Button } from "@/components/ui/button";
import { Trash2, Minus, Plus } from "lucide-react";

export default function Cart() {
  const { items, remove, updateQty, subtotal } = useCart();

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-32 text-center">
        <h1 className="font-serif-display text-5xl">Your cart is empty</h1>
        <p className="mt-4 font-store text-[#5C5C54]">Discover our herbal collection to get started.</p>
        <Button asChild className="mt-8 rounded-full h-12 px-8 bg-[#4A5D23] hover:bg-[#3D4D1D]">
          <Link to="/shop" data-testid="cart-empty-shop-link">Browse shop</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 lg:px-10 py-14">
      <h1 className="font-serif-display text-5xl">Cart</h1>
      <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 divide-y divide-[#E5E1D8]">
          {items.map((it) => (
            <div key={it.product_id} data-testid={`cart-item-${it.sku}`} className="py-6 flex gap-5">
              <img src={it.image_url} alt="" className="h-24 w-24 rounded-lg object-cover" />
              <div className="flex-1">
                <div className="font-serif-display text-xl">{it.name}</div>
                <div className="mt-1 font-mono-kh text-[10px] uppercase tracking-widest text-[#5C5C54]">{it.sku}</div>
                <div className="mt-3 flex items-center gap-3">
                  <div className="flex items-center border border-[#E5E1D8] rounded-full">
                    <button onClick={() => updateQty(it.product_id, it.quantity - 1)} className="h-9 w-9 grid place-items-center"><Minus className="h-3.5 w-3.5" /></button>
                    <div className="w-8 text-center font-mono-kh text-sm">{it.quantity}</div>
                    <button onClick={() => updateQty(it.product_id, it.quantity + 1)} className="h-9 w-9 grid place-items-center"><Plus className="h-3.5 w-3.5" /></button>
                  </div>
                  <button data-testid={`remove-${it.sku}`} onClick={() => remove(it.product_id)} className="text-[#A43026] hover:underline flex items-center gap-1 font-store text-sm">
                    <Trash2 className="h-4 w-4" /> Remove
                  </button>
                </div>
              </div>
              <div className="text-right">
                <div className="font-dash text-lg">₹{(it.price * it.quantity).toFixed(2)}</div>
                <div className="font-mono-kh text-[10px] text-[#5C5C54]">₹{it.price} × {it.quantity}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="lg:col-span-1">
          <div className="rounded-lg border border-[#E5E1D8] p-6 sticky top-24">
            <div className="font-dash text-sm text-[#5C5C54]">Order summary</div>
            <div className="mt-4 flex justify-between font-store"><span>Subtotal</span><span className="font-mono-kh">₹{subtotal.toFixed(2)}</span></div>
            <div className="mt-2 flex justify-between font-store text-[#5C5C54] text-sm"><span>GST</span><span>Computed at checkout</span></div>
            <div className="mt-2 flex justify-between font-store text-[#5C5C54] text-sm"><span>Shipping</span><span>Calculated at checkout</span></div>
            <Button asChild data-testid="proceed-checkout-btn" className="mt-6 w-full rounded-full h-12 bg-[#4A5D23] hover:bg-[#3D4D1D]">
              <Link to="/checkout">Proceed to checkout</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
