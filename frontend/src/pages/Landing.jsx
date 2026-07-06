import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Leaf, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";

const HERO_BG = "https://images.unsplash.com/photo-1573519716358-1cdc98533bfa?crop=entropy&cs=srgb&fm=jpg&w=2000&q=85";
const IMG_A = "https://images.unsplash.com/photo-1643067077447-78239a403a18?crop=entropy&cs=srgb&fm=jpg&w=1200&q=85";
const IMG_B = "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?crop=entropy&cs=srgb&fm=jpg&w=1200&q=85";
const IMG_C = "https://images.unsplash.com/photo-1613803745799-ba6c10aace85?crop=entropy&cs=srgb&fm=jpg&w=1200&q=85";

export default function Landing() {
  const [featured, setFeatured] = useState([]);
  useEffect(() => {
    api.get("/products", { params: { active_only: true } })
      .then(({ data }) => setFeatured(data.slice(0, 4)))
      .catch(() => {});
  }, []);

  return (
    <div className="relative">
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${HERO_BG})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#1C1C17]/40 via-[#1C1C17]/25 to-[#F9F8F6]" />
        <div className="relative mx-auto max-w-7xl px-6 lg:px-10 pt-24 pb-32 lg:pt-40 lg:pb-48">
          <div className="max-w-3xl animate-fade-up">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#F9F8F6]/90 border border-[#E5E1D8] font-mono-kh text-[10px] uppercase tracking-[0.24em] text-[#4A5D23]">
              <Leaf className="h-3 w-3" strokeWidth={1.5} /> Farm to bottle · India
            </div>
            <h1 className="mt-8 font-serif-display text-5xl sm:text-6xl lg:text-7xl leading-[0.95] text-[#F9F8F6]">
              Ancient herbs,<br />
              <span className="italic text-[#D4A373]">quietly modern</span> rituals.
            </h1>
            <p className="mt-6 font-store text-lg text-[#F9F8F6]/90 leading-relaxed max-w-xl">
              Kaya's Herbals blends Ayurvedic wisdom with rigorous, batch-tracked
              production — for wellness that's both honest and beautiful.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Button data-testid="hero-shop-btn" asChild className="rounded-full h-12 px-8 bg-[#4A5D23] hover:bg-[#3D4D1D] font-store">
                <Link to="/shop">Shop the collection</Link>
              </Button>
              <Button data-testid="hero-wholesale-btn" asChild variant="outline" className="rounded-full h-12 px-8 bg-[#F9F8F6]/10 backdrop-blur border-[#F9F8F6]/60 text-[#F9F8F6] hover:bg-[#F9F8F6]/20 hover:text-[#F9F8F6] font-store">
                <Link to="/register">Become a distributor</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* STATS STRIP */}
      <section className="mx-auto max-w-7xl px-6 lg:px-10 -mt-12 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 rounded-2xl bg-[#1C1C17] text-[#F9F8F6]">
          {[
            { k: "36", u: "Herbs sourced", s: "Across 9 Indian states" },
            { k: "12k+", u: "Retail customers", s: "Since 2019" },
            { k: "180", u: "Active distributors", s: "Pan-India network" },
            { k: "100%", u: "Batch tracked", s: "Field to shelf" },
          ].map((s, i) => (
            <div key={i} className="p-8 border-r last:border-r-0 border-[#F9F8F6]/10">
              <div className="font-serif-display text-5xl">{s.k}</div>
              <div className="mt-2 font-dash text-sm">{s.u}</div>
              <div className="mt-1 font-mono-kh text-[10px] tracking-widest uppercase text-[#F9F8F6]/60">{s.s}</div>
            </div>
          ))}
        </div>
      </section>

      {/* STORY / ASYMMETRIC */}
      <section id="story" className="mx-auto max-w-7xl px-6 lg:px-10 py-28">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-5 lg:sticky lg:top-32 self-start">
            <div className="font-mono-kh text-[10px] uppercase tracking-[0.28em] text-[#4A5D23]">Chapter I</div>
            <h2 className="mt-4 font-serif-display text-4xl lg:text-5xl leading-tight">
              A quieter kind of<br /> wellness.
            </h2>
            <p className="mt-6 font-store text-[#5C5C54] leading-relaxed">
              We built Kaya's around a single idea — Ayurveda deserves the same
              rigour we ask of modern medicine. Every batch is tested, traced
              and dated, so what reaches your ritual is exactly what left our fields.
            </p>
            <div className="mt-8 flex gap-3">
              <Sparkles className="h-5 w-5 text-[#C4654F]" strokeWidth={1.5} />
              <div className="font-store text-sm text-[#1C1C17]">Cold-processed · Small batch · Solvent free</div>
            </div>
          </div>
          <div className="col-span-12 lg:col-span-7 grid grid-cols-6 gap-4">
            <img src={IMG_A} alt="" className="col-span-4 aspect-[4/5] object-cover rounded-lg" />
            <img src={IMG_B} alt="" className="col-span-2 aspect-[3/5] object-cover rounded-lg mt-16" />
            <img src={IMG_C} alt="" className="col-span-3 aspect-square object-cover rounded-lg" />
            <div className="col-span-3 bg-[#F2EFE9] rounded-lg p-6 flex flex-col justify-end aspect-square">
              <div className="font-serif-display text-3xl">"Grounded in soil, guided by science."</div>
              <div className="mt-4 font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">— Kaya Founding Note</div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURED PRODUCTS */}
      <section className="bg-[#F2EFE9]">
        <div className="mx-auto max-w-7xl px-6 lg:px-10 py-24">
          <div className="flex items-end justify-between mb-14">
            <div>
              <div className="font-mono-kh text-[10px] uppercase tracking-[0.28em] text-[#4A5D23]">Chapter II</div>
              <h2 className="mt-3 font-serif-display text-4xl lg:text-5xl">The collection</h2>
            </div>
            <Link to="/shop" data-testid="see-all-products-link" className="hidden sm:inline-flex items-center gap-2 font-store text-sm text-[#1C1C17] tick-underline">
              See everything <ArrowUpRight className="h-4 w-4" strokeWidth={1.5} />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featured.map((p, idx) => (
              <Link
                to={`/product/${p.id}`}
                key={p.id}
                data-testid={`featured-product-${idx}`}
                className="group"
              >
                <div className="relative aspect-[4/5] overflow-hidden rounded-lg bg-[#F9F8F6]">
                  <img src={p.image_url} alt={p.name} className="w-full h-full object-cover transition duration-700 group-hover:scale-105" />
                  <div className="absolute top-3 left-3 px-2 py-1 rounded-full bg-[#F9F8F6]/85 backdrop-blur font-mono-kh text-[10px] tracking-widest uppercase">
                    {p.category}
                  </div>
                </div>
                <div className="mt-4 flex items-start justify-between gap-3">
                  <div>
                    <div className="font-serif-display text-xl leading-tight">{p.name}</div>
                    <div className="mt-1 font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">{p.sku}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-dash text-lg">₹{p.price}</div>
                    {p.mrp > p.price && <div className="font-mono-kh text-[10px] text-[#5C5C54] line-through">₹{p.mrp}</div>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* WHOLESALE CTA */}
      <section id="wholesale" className="mx-auto max-w-7xl px-6 lg:px-10 py-28">
        <div className="relative overflow-hidden rounded-2xl bg-[#4A5D23] text-[#F9F8F6] p-10 lg:p-16">
          <div className="grain-overlay" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 relative">
            <div>
              <div className="font-mono-kh text-[10px] uppercase tracking-[0.28em] text-[#D4A373]">Wholesale programme</div>
              <h2 className="mt-4 font-serif-display text-4xl lg:text-5xl leading-tight">
                Bring Kaya's<br /> to your shelves.
              </h2>
              <p className="mt-5 font-store text-[#F9F8F6]/85 leading-relaxed max-w-md">
                Volume-based pricing, dedicated ERP portal for order tracking, and
                GST-compliant invoices — all under one login.
              </p>
              <Button data-testid="wholesale-cta-btn" asChild className="mt-8 rounded-full h-12 px-8 bg-[#C4654F] hover:bg-[#a44f3d]">
                <Link to="/register">Apply for distribution</Link>
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                ["Silver", "Up to 10% off MRP"],
                ["Gold", "Up to 20% off MRP"],
                ["Platinum", "Up to 30% off MRP"],
                ["ERP portal", "Live order & invoice tracking"],
              ].map(([a, b], i) => (
                <div key={i} className="p-5 rounded-lg bg-[#F9F8F6]/8 border border-[#F9F8F6]/10">
                  <div className="font-dash text-sm">{a}</div>
                  <div className="mt-2 font-mono-kh text-[10px] tracking-widest uppercase text-[#F9F8F6]/70">{b}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
