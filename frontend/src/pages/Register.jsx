import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "sonner";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", phone: "", role: "customer" });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const res = await register(form);
    setBusy(false);
    if (res.ok) {
      toast.success("Account created");
      navigate("/");
    } else {
      toast.error(res.error);
    }
  };

  return (
    <div className="mx-auto max-w-md px-6 py-14">
      <div className="text-center">
        <h1 className="font-serif-display text-5xl">Create account</h1>
        <p className="mt-3 font-store text-[#5C5C54]">Join Kaya's Herbals</p>
      </div>
      <form onSubmit={submit} className="mt-8 space-y-4 bg-white p-8 rounded-2xl border border-[#E5E1D8]">
        <div>
          <Label>Full name</Label>
          <Input data-testid="register-name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 h-11" />
        </div>
        <div>
          <Label>Email</Label>
          <Input data-testid="register-email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 h-11" />
        </div>
        <div>
          <Label>Phone</Label>
          <Input data-testid="register-phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="mt-1 h-11" />
        </div>
        <div>
          <Label>Password</Label>
          <Input data-testid="register-password" type="password" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-1 h-11" />
        </div>
        <div>
          <Label>Account type</Label>
          <RadioGroup value={form.role} onValueChange={(v) => setForm({ ...form, role: v })} className="mt-2 grid grid-cols-2 gap-2">
            <label className={`p-3 border rounded-md cursor-pointer flex items-center gap-2 ${form.role === "customer" ? "border-[#4A5D23] bg-[#F2EFE9]" : "border-[#E5E1D8]"}`}>
              <RadioGroupItem data-testid="role-customer" value="customer" /> <span className="font-store text-sm">Customer</span>
            </label>
            <label className={`p-3 border rounded-md cursor-pointer flex items-center gap-2 ${form.role === "distributor" ? "border-[#4A5D23] bg-[#F2EFE9]" : "border-[#E5E1D8]"}`}>
              <RadioGroupItem data-testid="role-distributor" value="distributor" /> <span className="font-store text-sm">Distributor</span>
            </label>
          </RadioGroup>
        </div>
        <Button data-testid="register-submit" type="submit" disabled={busy} className="w-full h-12 rounded-full bg-[#4A5D23] hover:bg-[#3D4D1D] font-store">
          {busy ? "Creating…" : "Create account"}
        </Button>
        <div className="text-center font-store text-sm text-[#5C5C54]">
          Already have an account? <Link to="/login" className="text-[#4A5D23] hover:underline">Sign in</Link>
        </div>
      </form>
    </div>
  );
}
