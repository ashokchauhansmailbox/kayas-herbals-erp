import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const res = await login(form.email, form.password);
    setBusy(false);
    if (res.ok) {
      toast.success("Welcome back");
      const dest = res.user.role === "admin" || res.user.role === "staff" ? "/admin" : "/";
      navigate(dest);
    } else {
      toast.error(res.error);
    }
  };

  return (
    <div className="mx-auto max-w-md px-6 py-20">
      <div className="text-center">
        <h1 className="font-serif-display text-5xl">Welcome back</h1>
        <p className="mt-3 font-store text-[#5C5C54]">Sign in to your Kaya's account</p>
      </div>
      <form onSubmit={submit} className="mt-10 space-y-5 bg-white p-8 rounded-2xl border border-[#E5E1D8]">
        <div>
          <Label htmlFor="email">Email</Label>
          <Input data-testid="login-email" id="email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 h-11" />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input data-testid="login-password" id="password" type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-1 h-11" />
        </div>
        <Button data-testid="login-submit" type="submit" disabled={busy} className="w-full h-12 rounded-full bg-[#4A5D23] hover:bg-[#3D4D1D] font-store">
          {busy ? "Signing in…" : "Sign in"}
        </Button>
        <div className="text-center font-store text-sm text-[#5C5C54]">
          New here? <Link to="/register" className="text-[#4A5D23] hover:underline">Create an account</Link>
        </div>
      </form>
    </div>
  );
}
