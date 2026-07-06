import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Printer } from "lucide-react";

export default function InvoicesAdmin() {
  const [rows, setRows] = useState([]);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    api.get("/invoices").then(({ data }) => setRows(data)).catch(() => {});
  }, []);

  return (
    <div>
      <div className="mb-6">
        <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Billing</div>
        <h1 className="font-dash font-bold text-3xl mt-1">Invoices & GST</h1>
      </div>

      <div className="bg-white border border-[#E5E1D8] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[#F2EFE9] font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
            <tr>
              <th className="text-left p-3">Invoice #</th>
              <th className="text-left p-3">Order #</th>
              <th className="text-left p-3">Customer</th>
              <th className="text-left p-3">Date</th>
              <th className="text-right p-3">CGST</th>
              <th className="text-right p-3">SGST</th>
              <th className="text-right p-3">IGST</th>
              <th className="text-right p-3">Total</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody className="font-store">
            {rows.length === 0 && <tr><td colSpan={9} className="p-8 text-center text-[#5C5C54]">No invoices yet. Generate one from Orders.</td></tr>}
            {rows.map((inv) => (
              <tr key={inv.id} data-testid={`inv-row-${inv.invoice_number}`} className="border-t border-[#E5E1D8]">
                <td className="p-3 font-mono-kh text-xs">{inv.invoice_number}</td>
                <td className="p-3 font-mono-kh text-xs">{inv.order_number}</td>
                <td className="p-3">{inv.customer_name}</td>
                <td className="p-3 text-[#5C5C54] font-mono-kh text-xs">{new Date(inv.created_at).toLocaleDateString()}</td>
                <td className="p-3 text-right font-mono-kh">₹{inv.cgst_total.toFixed(2)}</td>
                <td className="p-3 text-right font-mono-kh">₹{inv.sgst_total.toFixed(2)}</td>
                <td className="p-3 text-right font-mono-kh">₹{inv.igst_total.toFixed(2)}</td>
                <td className="p-3 text-right font-mono-kh font-bold">₹{inv.grand_total.toFixed(2)}</td>
                <td className="p-3 text-right">
                  <Button size="sm" variant="outline" onClick={() => setDetail(inv)} data-testid={`view-inv-${inv.invoice_number}`}>View</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={!!detail} onOpenChange={(v) => !v && setDetail(null)}>
        <DialogContent className="bg-white max-w-3xl print:shadow-none">
          <DialogHeader>
            <DialogTitle className="font-dash flex items-center justify-between">
              Invoice
              <Button size="sm" variant="outline" onClick={() => window.print()} className="ml-4"><Printer className="h-3.5 w-3.5 mr-1" /> Print</Button>
            </DialogTitle>
          </DialogHeader>
          {detail && (
            <div className="font-store text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="font-serif-display text-2xl">Kaya's Herbals</div>
                  <div className="text-xs text-[#5C5C54]">Bengaluru, India · GSTIN 29AAAAA0000A1Z5</div>
                </div>
                <div className="text-right">
                  <div className="font-mono-kh text-xs uppercase tracking-widest text-[#5C5C54]">Invoice</div>
                  <div className="font-mono-kh">{detail.invoice_number}</div>
                  <div className="font-mono-kh text-xs mt-2">{new Date(detail.created_at).toLocaleDateString()}</div>
                </div>
              </div>
              <div className="border-t border-[#E5E1D8] mt-4 pt-4 grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-[#5C5C54] uppercase tracking-widest">Bill to</div>
                  <div>{detail.customer_name}</div>
                  <div className="text-xs text-[#5C5C54]">{detail.customer_email}</div>
                  <div className="text-xs text-[#5C5C54] mt-1">{detail.shipping_address}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-[#5C5C54] uppercase tracking-widest">Order</div>
                  <div className="font-mono-kh">{detail.order_number}</div>
                  <div className="mt-2 text-xs text-[#5C5C54] uppercase tracking-widest">GST Mode</div>
                  <div className="font-mono-kh">{detail.is_interstate ? "IGST" : "CGST + SGST"}</div>
                </div>
              </div>
              <table className="w-full mt-6 text-sm">
                <thead className="bg-[#F2EFE9] font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">
                  <tr>
                    <th className="text-left p-2">Item</th>
                    <th className="text-right p-2">Qty</th>
                    <th className="text-right p-2">Unit</th>
                    <th className="text-right p-2">GST%</th>
                    <th className="text-right p-2">Tax</th>
                    <th className="text-right p-2">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.items.map((i, idx) => (
                    <tr key={idx} className="border-t border-[#E5E1D8]">
                      <td className="p-2"><div>{i.name}</div><div className="font-mono-kh text-[10px] text-[#5C5C54]">{i.sku}</div></td>
                      <td className="text-right p-2 font-mono-kh">{i.quantity}</td>
                      <td className="text-right p-2 font-mono-kh">₹{i.unit_price.toFixed(2)}</td>
                      <td className="text-right p-2 font-mono-kh">{i.gst_rate}%</td>
                      <td className="text-right p-2 font-mono-kh">₹{i.tax_total.toFixed(2)}</td>
                      <td className="text-right p-2 font-mono-kh">₹{i.line_total.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-4 border-t border-[#E5E1D8] pt-4 flex justify-end">
                <div className="w-64 space-y-1">
                  <div className="flex justify-between"><span>Subtotal</span><span className="font-mono-kh">₹{detail.subtotal.toFixed(2)}</span></div>
                  {!detail.is_interstate && <>
                    <div className="flex justify-between"><span>CGST</span><span className="font-mono-kh">₹{detail.cgst_total.toFixed(2)}</span></div>
                    <div className="flex justify-between"><span>SGST</span><span className="font-mono-kh">₹{detail.sgst_total.toFixed(2)}</span></div>
                  </>}
                  {detail.is_interstate && <div className="flex justify-between"><span>IGST</span><span className="font-mono-kh">₹{detail.igst_total.toFixed(2)}</span></div>}
                  <div className="flex justify-between font-bold border-t border-[#E5E1D8] pt-1 mt-1"><span>Grand total</span><span className="font-mono-kh">₹{detail.grand_total.toFixed(2)}</span></div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
