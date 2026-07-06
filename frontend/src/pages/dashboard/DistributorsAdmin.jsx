import React, { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Edit, Trash2 } from "lucide-react";
import { toast } from "sonner";

const empty = { name: "", email: "", phone: "", company: "", gstin: "", address: "", tier: "silver", discount_pct: 0, credit_limit: 0 };

export default function DistributorsAdmin() {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);

  const load = () => api.get("/distributors").then(({ data }) => setRows(data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const startNew = () => { setEditing(null); setForm(empty); setOpen(true); };
  const startEdit = (d) => {
    setEditing(d);
    setForm({ ...empty, ...d });
    setOpen(true);
  };

  const submit = async () => {
    try {
      const payload = { ...form, discount_pct: Number(form.discount_pct), credit_limit: Number(form.credit_limit) };
      if (editing) await api.put(`/distributors/${editing.id}`, payload);
      else await api.post("/distributors", payload);
      toast.success(editing ? "Distributor updated" : "Distributor added");
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const del = async (d) => {
    if (!window.confirm(`Delete ${d.name}?`)) return;
    try { await api.delete(`/distributors/${d.id}`); load(); toast.success("Removed"); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Partners</div>
          <h1 className="font-dash font-bold text-3xl mt-1">Distributors</h1>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="new-distributor-btn" onClick={startNew} className="rounded-md bg-[#4A5D23] hover:bg-[#3D4D1D]">
              <Plus className="h-4 w-4 mr-2" /> New distributor
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl bg-white">
            <DialogHeader><DialogTitle className="font-dash">{editing ? "Edit distributor" : "New distributor"}</DialogTitle></DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Name</Label><Input data-testid="dist-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div><Label>Company</Label><Input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></div>
              <div><Label>Email</Label><Input data-testid="dist-email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
              <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
              <div><Label>GSTIN</Label><Input value={form.gstin} onChange={(e) => setForm({ ...form, gstin: e.target.value })} /></div>
              <div>
                <Label>Tier</Label>
                <Select value={form.tier} onValueChange={(v) => setForm({ ...form, tier: v })}>
                  <SelectTrigger data-testid="dist-tier"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="silver">Silver</SelectItem>
                    <SelectItem value="gold">Gold</SelectItem>
                    <SelectItem value="platinum">Platinum</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Discount %</Label><Input type="number" value={form.discount_pct} onChange={(e) => setForm({ ...form, discount_pct: e.target.value })} /></div>
              <div><Label>Credit limit (₹)</Label><Input type="number" value={form.credit_limit} onChange={(e) => setForm({ ...form, credit_limit: e.target.value })} /></div>
              <div className="col-span-2"><Label>Address</Label><Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
            </div>
            <DialogFooter><Button data-testid="save-dist-btn" onClick={submit} className="bg-[#4A5D23] hover:bg-[#3D4D1D]">Save</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white border border-[#E5E1D8] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[#F2EFE9] font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
            <tr>
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Company</th>
              <th className="text-left p-3">Contact</th>
              <th className="text-left p-3">GSTIN</th>
              <th className="text-right p-3">Tier</th>
              <th className="text-right p-3">Discount</th>
              <th className="text-right p-3"></th>
            </tr>
          </thead>
          <tbody className="font-store">
            {rows.length === 0 && <tr><td colSpan={7} className="p-8 text-center text-[#5C5C54]">No distributors yet. Click "New distributor" to add one.</td></tr>}
            {rows.map((d) => (
              <tr key={d.id} data-testid={`dist-row-${d.email}`} className="border-t border-[#E5E1D8]">
                <td className="p-3">{d.name}</td>
                <td className="p-3 text-[#5C5C54]">{d.company}</td>
                <td className="p-3 text-[#5C5C54]"><div>{d.email}</div><div className="font-mono-kh text-xs">{d.phone}</div></td>
                <td className="p-3 font-mono-kh text-xs">{d.gstin || "—"}</td>
                <td className="p-3 text-right"><span className="px-2 py-0.5 rounded-full font-mono-kh text-[10px] uppercase tracking-widest bg-[#F2EFE9]">{d.tier}</span></td>
                <td className="p-3 text-right font-mono-kh">{d.discount_pct}%</td>
                <td className="p-3 text-right whitespace-nowrap">
                  <button onClick={() => startEdit(d)} className="p-1.5 hover:bg-[#F2EFE9] rounded-md mr-1"><Edit className="h-4 w-4" /></button>
                  <button onClick={() => del(d)} className="p-1.5 hover:bg-[#F2EFE9] rounded-md text-[#A43026]"><Trash2 className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
