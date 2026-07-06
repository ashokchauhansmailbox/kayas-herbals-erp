import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Minus, Plus, ShoppingBag, Leaf } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { toast } from "sonner";

export default function ProductDetail() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [qty, setQty] = useState(1);
  const { add } = useCart();
  const navigate = useNavigate();

  useEffect(() => {
    api.get(`/products/${id}`).then(({ data }) => setP(data)).catch(() => setP(false));
  }, [id]);

  if (p === null) return <div className="py-32 text-center font-store text-[#5C5C54]">Loading…</div>;
  if (!p) return <div className="py-32 text-center font-store text-[#5C5C54]">Product not found.</div>;

  const outOfStock = p.stock <= 0;

  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-10 py-14">
      <Link to="/shop" className="font-mono-kh text-[10px] uppercase tracking-[0.28em] text-[#5C5C54] hover:text-[#4A5D23]">← Back to shop</Link>
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="relative aspect-square lg:aspect-[4/5] overflow-hidden rounded-2xl bg-[#F2EFE9]">
          <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
        </div>
        <div>
          <div className="font-mono-kh text-[10px] uppercase tracking-[0.28em] text-[#4A5D23]">{p.category}</div>
          <h1 className="mt-4 font-serif-display text-5xl leading-tight">{p.name}</h1>
          <div className="mt-4 font-mono-kh text-[11px] tracking-widest uppercase text-[#5C5C54]">SKU · {p.sku}</div>
          <div className="mt-8 flex items-baseline gap-4">
            <div className="font-dash font-bold text-4xl">₹{p.price}</div>
            {p.mrp > p.price && <div className="font-mono-kh text-sm text-[#5C5C54] line-through">₹{p.mrp}</div>}
            <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">incl. {p.gst_rate}% GST</div>
          </div>
          <p className="mt-8 font-store text-[#5C5C54] leading-relaxed">{p.description}</p>

          <div className="mt-10 flex items-center gap-4">
            <div className="flex items-center border border-[#E5E1D8] rounded-full overflow-hidden">
              <button data-testid="qty-decrement" onClick={() => setQty((q) => Math.max(1, q - 1))} className="h-11 w-11 grid place-items-center hover:bg-[#F2EFE9]">
                <Minus className="h-4 w-4" strokeWidth={1.5} />
              </button>
              <div data-testid="qty-display" className="w-10 text-center font-mono-kh">{qty}</div>
              <button data-testid="qty-increment" onClick={() => setQty((q) => q + 1)} className="h-11 w-11 grid place-items-center hover:bg-[#F2EFE9]">
                <Plus className="h-4 w-4" strokeWidth={1.5} />
              </button>
            </div>
            <Button
              data-testid="add-to-cart-btn"
              disabled={outOfStock}
              onClick={() => {
                add(p, qty);
                toast.success(`Added ${qty} × ${p.name} to cart`);
              }}
              className="rounded-full h-12 px-8 bg-[#4A5D23] hover:bg-[#3D4D1D] font-store"
            >
              <ShoppingBag className="h-4 w-4 mr-2" strokeWidth={1.5} />
              {outOfStock ? "Out of stock" : "Add to cart"}
            </Button>
            <Button
              data-testid="buy-now-btn"
              disabled={outOfStock}
              variant="outline"
              onClick={() => {
                add(p, qty);
                navigate("/checkout");
              }}
              className="rounded-full h-12 px-8 font-store"
            >
              Buy now
            </Button>
          </div>

          <div className="mt-12 grid grid-cols-3 gap-4">
            {[
              ["Solvent free", "Cold-processed"],
              ["Batch tested", "Fully traceable"],
              ["Ships in 24h", "Across India"],
            ].map(([a, b], i) => (
              <div key={i} className="p-4 rounded-lg bg-[#F2EFE9]">
                <Leaf className="h-4 w-4 text-[#4A5D23]" strokeWidth={1.5} />
                <div className="mt-2 font-dash text-sm">{a}</div>
                <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">{b}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
