import React, { useEffect, useState, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export default function Shop() {
  const [products, setProducts] = useState([]);
  const [cats, setCats] = useState([]);
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const category = params.get("category") || "";

  useEffect(() => {
    api.get("/products", { params: { active_only: true, q: q || undefined, category: category || undefined } })
      .then(({ data }) => setProducts(data)).catch(() => {});
    api.get("/categories").then(({ data }) => setCats(data)).catch(() => {});
  }, [q, category]);

  const setParam = (k, v) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next);
  };

  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-10 py-14">
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 mb-10">
        <div>
          <div className="font-mono-kh text-[10px] uppercase tracking-[0.28em] text-[#4A5D23]">Shop</div>
          <h1 className="mt-3 font-serif-display text-5xl">The collection</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            data-testid="filter-all"
            onClick={() => setParam("category", "")}
            className={`px-4 h-9 rounded-full font-store text-sm border transition ${!category ? "bg-[#1C1C17] text-[#F9F8F6] border-[#1C1C17]" : "border-[#E5E1D8] hover:bg-[#F2EFE9]"}`}
          >
            All
          </button>
          {cats.map((c) => (
            <button
              key={c}
              data-testid={`filter-${c.toLowerCase()}`}
              onClick={() => setParam("category", c)}
              className={`px-4 h-9 rounded-full font-store text-sm border transition ${category === c ? "bg-[#1C1C17] text-[#F9F8F6] border-[#1C1C17]" : "border-[#E5E1D8] hover:bg-[#F2EFE9]"}`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-8 max-w-md">
        <Input
          data-testid="shop-search-input"
          placeholder="Search by name or SKU…"
          value={q}
          onChange={(e) => setParam("q", e.target.value)}
          className="rounded-full h-11 bg-white border-[#E5E1D8] font-store"
        />
      </div>

      {products.length === 0 ? (
        <div className="py-32 text-center font-store text-[#5C5C54]">No products match.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {products.map((p) => (
            <Link
              key={p.id}
              to={`/product/${p.id}`}
              data-testid={`product-card-${p.sku}`}
              className="group"
            >
              <div className="relative aspect-[4/5] overflow-hidden rounded-lg bg-[#F2EFE9]">
                <img src={p.image_url} alt={p.name} className="w-full h-full object-cover transition duration-700 group-hover:scale-105" />
                {p.stock <= p.low_stock_threshold && (
                  <Badge className="absolute top-3 right-3 bg-[#C4654F] hover:bg-[#C4654F] rounded-full font-mono-kh text-[10px] tracking-widest">LOW STOCK</Badge>
                )}
              </div>
              <div className="mt-4 flex items-start justify-between gap-3">
                <div>
                  <div className="font-serif-display text-xl leading-tight">{p.name}</div>
                  <div className="mt-1 font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">{p.sku} · {p.category}</div>
                </div>
                <div className="text-right">
                  <div className="font-dash text-lg">₹{p.price}</div>
                  {p.mrp > p.price && <div className="font-mono-kh text-[10px] text-[#5C5C54] line-through">₹{p.mrp}</div>}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
