import React, { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Edit, Trash2 } from "lucide-react";
import { toast } from "sonner";

const empty = {
  name: "", sku: "", category: "", description: "", mrp: 0, price: 0,
  distributor_price: 0, stock: 0, gst_rate: 5, image_url: "", low_stock_threshold: 10, active: true,
};

export default function ProductsAdmin() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);

  const load = () => api.get("/products").then(({ data }) => setItems(data));
  useEffect(() => { load(); }, []);

  const startNew = () => { setEditing(null); setForm(empty); setOpen(true); };
  const startEdit = (p) => {
    setEditing(p);
    setForm({
      name: p.name, sku: p.sku, category: p.category, description: p.description || "",
      mrp: p.mrp, price: p.price, distributor_price: p.distributor_price || 0, stock: p.stock,
      gst_rate: p.gst_rate, image_url: p.image_url || "", low_stock_threshold: p.low_stock_threshold, active: p.active,
    });
    setOpen(true);
  };

  const submit = async () => {
    try {
      const payload = {
        ...form,
        mrp: Number(form.mrp), price: Number(form.price),
        distributor_price: Number(form.distributor_price) || null,
        stock: Number(form.stock), gst_rate: Number(form.gst_rate),
        low_stock_threshold: Number(form.low_stock_threshold),
      };
      if (editing) await api.put(`/products/${editing.id}`, payload);
      else await api.post("/products", payload);
      toast.success(editing ? "Product updated" : "Product created");
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || e.message);
    }
  };

  const del = async (p) => {
    if (!window.confirm(`Delete ${p.name}?`)) return;
    try { await api.delete(`/products/${p.id}`); load(); toast.success("Deleted"); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Catalog</div>
          <h1 className="font-dash font-bold text-3xl mt-1">Products</h1>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="new-product-btn" onClick={startNew} className="rounded-md bg-[#4A5D23] hover:bg-[#3D4D1D]">
              <Plus className="h-4 w-4 mr-2" /> New product
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl bg-white">
            <DialogHeader>
              <DialogTitle className="font-dash">{editing ? "Edit product" : "New product"}</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2"><Label>Name</Label><Input data-testid="product-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div><Label>SKU</Label><Input data-testid="product-sku" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} /></div>
              <div><Label>Category</Label><Input data-testid="product-category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></div>
              <div className="col-span-2"><Label>Description</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} /></div>
              <div><Label>MRP (₹)</Label><Input type="number" value={form.mrp} onChange={(e) => setForm({ ...form, mrp: e.target.value })} /></div>
              <div><Label>Selling price (₹)</Label><Input data-testid="product-price" type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></div>
              <div><Label>Distributor price (₹)</Label><Input type="number" value={form.distributor_price} onChange={(e) => setForm({ ...form, distributor_price: e.target.value })} /></div>
              <div><Label>GST rate (%)</Label><Input type="number" value={form.gst_rate} onChange={(e) => setForm({ ...form, gst_rate: e.target.value })} /></div>
              <div><Label>Stock</Label><Input data-testid="product-stock" type="number" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} /></div>
              <div><Label>Low-stock threshold</Label><Input type="number" value={form.low_stock_threshold} onChange={(e) => setForm({ ...form, low_stock_threshold: e.target.value })} /></div>
              <div className="col-span-2"><Label>Image URL</Label><Input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." /></div>
              <div className="flex items-center gap-3"><Switch checked={form.active} onCheckedChange={(v) => setForm({ ...form, active: v })} /><Label className="cursor-pointer">Active</Label></div>
            </div>
            <DialogFooter>
              <Button data-testid="save-product-btn" onClick={submit} className="bg-[#4A5D23] hover:bg-[#3D4D1D]">Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white border border-[#E5E1D8] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[#F2EFE9] font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
            <tr>
              <th className="text-left p-3">SKU</th>
              <th className="text-left p-3">Product</th>
              <th className="text-left p-3">Category</th>
              <th className="text-right p-3">Price</th>
              <th className="text-right p-3">Stock</th>
              <th className="text-right p-3">GST</th>
              <th className="text-right p-3">Status</th>
              <th className="text-right p-3"></th>
            </tr>
          </thead>
          <tbody className="font-store">
            {items.map((p) => (
              <tr key={p.id} data-testid={`product-row-${p.sku}`} className="border-t border-[#E5E1D8]">
                <td className="p-3 font-mono-kh text-xs">{p.sku}</td>
                <td className="p-3">{p.name}</td>
                <td className="p-3 text-[#5C5C54]">{p.category}</td>
                <td className="p-3 text-right font-mono-kh">₹{p.price}</td>
                <td className={`p-3 text-right font-mono-kh ${p.stock <= p.low_stock_threshold ? "text-[#A43026] font-bold" : ""}`}>{p.stock}</td>
                <td className="p-3 text-right font-mono-kh">{p.gst_rate}%</td>
                <td className="p-3 text-right">
                  <span className={`px-2 py-0.5 rounded-full font-mono-kh text-[10px] tracking-widest uppercase ${p.active ? "bg-[#4A5D23] text-white" : "bg-[#E5E1D8] text-[#5C5C54]"}`}>
                    {p.active ? "active" : "hidden"}
                  </span>
                </td>
                <td className="p-3 text-right whitespace-nowrap">
                  <button onClick={() => startEdit(p)} data-testid={`edit-${p.sku}`} className="p-1.5 hover:bg-[#F2EFE9] rounded-md mr-1"><Edit className="h-4 w-4" /></button>
                  <button onClick={() => del(p)} data-testid={`delete-${p.sku}`} className="p-1.5 hover:bg-[#F2EFE9] rounded-md text-[#A43026]"><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
