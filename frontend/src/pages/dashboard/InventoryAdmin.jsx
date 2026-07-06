import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export default function InventoryAdmin() {
  const [items, setItems] = useState([]);
  const [deltas, setDeltas] = useState({});

  const load = () => api.get("/products").then(({ data }) => setItems(data));
  useEffect(() => { load(); }, []);

  const adjust = async (id) => {
    const d = Number(deltas[id]);
    if (!d) return;
    try {
      await api.post(`/products/${id}/stock`, null, { params: { delta: d } });
      toast.success("Stock updated");
      setDeltas({ ...deltas, [id]: "" });
      load();
    } catch (e) {
      toast.error("Failed to adjust stock");
    }
  };

  const totalUnits = items.reduce((s, i) => s + i.stock, 0);
  const lowCount = items.filter((i) => i.stock <= i.low_stock_threshold).length;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-6">
        <div>
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Warehouse</div>
          <h1 className="font-dash font-bold text-3xl mt-1">Inventory</h1>
        </div>
        <div className="flex gap-6 font-mono-kh text-xs">
          <div><span className="text-[#5C5C54] uppercase tracking-widest">Units</span> <span className="text-lg font-bold ml-2">{totalUnits}</span></div>
          <div><span className="text-[#5C5C54] uppercase tracking-widest">Low</span> <span className="text-lg font-bold ml-2 text-[#A43026]">{lowCount}</span></div>
        </div>
      </div>

      <div className="bg-white border border-[#E5E1D8] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[#F2EFE9] font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
            <tr>
              <th className="text-left p-3">SKU</th>
              <th className="text-left p-3">Product</th>
              <th className="text-right p-3">Stock</th>
              <th className="text-right p-3">Threshold</th>
              <th className="text-right p-3">Adjust (± units)</th>
              <th></th>
            </tr>
          </thead>
          <tbody className="font-store">
            {items.map((p) => (
              <tr key={p.id} data-testid={`inv-row-${p.sku}`} className="border-t border-[#E5E1D8]">
                <td className="p-3 font-mono-kh text-xs">{p.sku}</td>
                <td className="p-3">{p.name}</td>
                <td className={`p-3 text-right font-mono-kh ${p.stock <= p.low_stock_threshold ? "text-[#A43026] font-bold" : ""}`}>{p.stock}</td>
                <td className="p-3 text-right font-mono-kh text-[#5C5C54]">{p.low_stock_threshold}</td>
                <td className="p-3 text-right">
                  <Input
                    type="number"
                    placeholder="±"
                    className="inline-block w-24 h-8 text-right font-mono-kh"
                    value={deltas[p.id] || ""}
                    onChange={(e) => setDeltas({ ...deltas, [p.id]: e.target.value })}
                    data-testid={`inv-delta-${p.sku}`}
                  />
                </td>
                <td className="p-3 text-right">
                  <Button size="sm" data-testid={`inv-apply-${p.sku}`} onClick={() => adjust(p.id)} className="h-8 bg-[#4A5D23] hover:bg-[#3D4D1D]">Apply</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
