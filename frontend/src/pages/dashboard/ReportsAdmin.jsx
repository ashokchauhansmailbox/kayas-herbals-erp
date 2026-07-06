import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function ReportsAdmin() {
  const [days, setDays] = useState("30");
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api.get("/reports/sales", { params: { days: Number(days) } })
      .then(({ data }) => setRows(data)).catch(() => {});
  }, [days]);

  const totalRevenue = rows.reduce((s, r) => s + r.revenue, 0);
  const totalOrders = rows.reduce((s, r) => s + r.orders, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Analytics</div>
          <h1 className="font-dash font-bold text-3xl mt-1">Reports</h1>
        </div>
        <Select value={days} onValueChange={setDays}>
          <SelectTrigger data-testid="report-range" className="w-40 bg-white"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
            <SelectItem value="365">Last year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="p-5 bg-white border border-[#E5E1D8] rounded-lg">
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Revenue</div>
          <div className="mt-2 font-dash font-bold text-3xl">₹{totalRevenue.toLocaleString()}</div>
        </div>
        <div className="p-5 bg-white border border-[#E5E1D8] rounded-lg">
          <div className="font-mono-kh text-[10px] tracking-widest uppercase text-[#5C5C54]">Orders</div>
          <div className="mt-2 font-dash font-bold text-3xl">{totalOrders}</div>
        </div>
      </div>

      <div className="p-5 bg-white border border-[#E5E1D8] rounded-lg">
        <div className="font-dash font-bold mb-4">Daily revenue</div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E1D8" />
              <XAxis dataKey="date" stroke="#5C5C54" fontSize={11} />
              <YAxis stroke="#5C5C54" fontSize={11} />
              <Tooltip contentStyle={{ background: "#F9F8F6", border: "1px solid #E5E1D8" }} />
              <Bar dataKey="revenue" fill="#4A5D23" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
