import React, { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const STATUS_COLORS = {
  pending: "bg-[#D4A373] text-white",
  processing: "bg-[#4A5D23] text-white",
  shipped: "bg-[#365E32] text-white",
  delivered: "bg-[#4A5D23] text-white",
  cancelled: "bg-[#A43026] text-white",
};

export default function OrdersAdmin() {
  const [rows, setRows] = useState([]);
  const [invoiceModal, setInvoiceModal] = useState(null);
  const [isInterstate, setIsInterstate] = useState(false);
  const [detail, setDetail] = useState(null);

  const load = () => api.get("/orders").then(({ data }) => setRows(data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const updateStatus = async (id, status) => {
    try { await api.put(`/orders/${id}/status`, null, { params: { status } }); toast.success("Status updated"); load(); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const genInvoice = async () => {
    try {
      const { data } = await api.post("/invoices", { order_id: invoiceModal.id, is_interstate: isInterstate });
      toast.success(`Invoice ${data.invoice_number} generated`);
      setInvoiceModal(null);
      setIsInterstate(false);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div>
      <div className="mb-6">
        <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Sales</div>
        <h1 className="font-dash font-bold text-3xl mt-1">Orders</h1>
      </div>

      <div className="bg-white border border-[#E5E1D8] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[#F2EFE9] font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
            <tr>
              <th className="text-left p-3">Order #</th>
              <th className="text-left p-3">Customer</th>
              <th className="text-left p-3">Type</th>
              <th className="text-right p-3">Items</th>
              <th className="text-right p-3">Total</th>
              <th className="text-right p-3">Status</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody className="font-store">
            {rows.length === 0 && <tr><td colSpan={7} className="p-8 text-center text-[#5C5C54]">No orders yet.</td></tr>}
            {rows.map((o) => (
              <tr key={o.id} data-testid={`order-row-${o.order_number}`} className="border-t border-[#E5E1D8]">
                <td className="p-3 font-mono-kh text-xs">{o.order_number}</td>
                <td className="p-3"><div>{o.customer_name}</div><div className="text-xs text-[#5C5C54]">{o.customer_email}</div></td>
                <td className="p-3 text-[#5C5C54]"><span className="px-2 py-0.5 rounded-full font-mono-kh text-[10px] uppercase tracking-widest bg-[#F2EFE9]">{o.order_type}</span></td>
                <td className="p-3 text-right font-mono-kh">{o.items.length}</td>
                <td className="p-3 text-right font-mono-kh">₹{o.grand_total.toFixed(2)}</td>
                <td className="p-3 text-right">
                  <Select value={o.status} onValueChange={(v) => updateStatus(o.id, v)}>
                    <SelectTrigger data-testid={`status-select-${o.order_number}`} className={`h-8 w-32 rounded-full border-0 justify-center font-mono-kh text-[10px] tracking-widest uppercase ${STATUS_COLORS[o.status]}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="processing">Processing</SelectItem>
                      <SelectItem value="shipped">Shipped</SelectItem>
                      <SelectItem value="delivered">Delivered</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </td>
                <td className="p-3 text-right whitespace-nowrap">
                  <Button size="sm" variant="outline" data-testid={`view-order-${o.order_number}`} onClick={() => setDetail(o)} className="mr-2">View</Button>
                  <Button size="sm" data-testid={`invoice-order-${o.order_number}`} onClick={() => setInvoiceModal(o)} className="bg-[#4A5D23] hover:bg-[#3D4D1D]">Invoice</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={!!invoiceModal} onOpenChange={(v) => !v && setInvoiceModal(null)}>
        <DialogContent className="bg-white">
          <DialogHeader><DialogTitle className="font-dash">Generate GST Invoice</DialogTitle></DialogHeader>
          {invoiceModal && (
            <div className="space-y-3">
              <div className="font-store text-sm">Order: <span className="font-mono-kh">{invoiceModal.order_number}</span></div>
              <div className="font-store text-sm">Amount: <span className="font-mono-kh">₹{invoiceModal.grand_total.toFixed(2)}</span></div>
              <div className="flex items-center gap-3 mt-4">
                <Switch data-testid="interstate-switch" checked={isInterstate} onCheckedChange={setIsInterstate} />
                <Label className="cursor-pointer">Interstate (apply IGST instead of CGST + SGST)</Label>
              </div>
            </div>
          )}
          <DialogFooter><Button data-testid="confirm-invoice-btn" onClick={genInvoice} className="bg-[#4A5D23] hover:bg-[#3D4D1D]">Generate</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!detail} onOpenChange={(v) => !v && setDetail(null)}>
        <DialogContent className="bg-white max-w-2xl">
          <DialogHeader><DialogTitle className="font-dash">Order details</DialogTitle></DialogHeader>
          {detail && (
            <div className="space-y-4 font-store text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div><div className="text-xs text-[#5C5C54]">Order</div><div className="font-mono-kh">{detail.order_number}</div></div>
                <div><div className="text-xs text-[#5C5C54]">Placed</div><div className="font-mono-kh">{new Date(detail.created_at).toLocaleString()}</div></div>
                <div><div className="text-xs text-[#5C5C54]">Customer</div><div>{detail.customer_name}</div><div className="text-xs">{detail.customer_email} · {detail.customer_phone}</div></div>
                <div><div className="text-xs text-[#5C5C54]">Ship to</div><div>{detail.shipping_address}</div></div>
              </div>
              <div className="border-t border-[#E5E1D8] pt-3">
                {detail.items.map((i, idx) => (
                  <div key={idx} className="flex justify-between py-1">
                    <span>{i.name} × {i.quantity}</span>
                    <span className="font-mono-kh">₹{i.line_total.toFixed(2)}</span>
                  </div>
                ))}
                <div className="border-t border-[#E5E1D8] pt-2 mt-2 space-y-1">
                  <div className="flex justify-between"><span>Subtotal</span><span className="font-mono-kh">₹{detail.subtotal.toFixed(2)}</span></div>
                  <div className="flex justify-between"><span>GST</span><span className="font-mono-kh">₹{detail.gst_total.toFixed(2)}</span></div>
                  <div className="flex justify-between font-bold text-base"><span>Total</span><span className="font-mono-kh">₹{detail.grand_total.toFixed(2)}</span></div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
