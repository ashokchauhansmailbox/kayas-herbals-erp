import React, { createContext, useContext, useEffect, useState } from "react";

const CartContext = createContext(null);
const KEY = "kh_cart";

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (_) { return []; }
  });

  useEffect(() => { localStorage.setItem(KEY, JSON.stringify(items)); }, [items]);

  const add = (product, qty = 1) => {
    setItems((prev) => {
      const exists = prev.find((i) => i.product_id === product.id);
      if (exists) {
        return prev.map((i) => i.product_id === product.id ? { ...i, quantity: i.quantity + qty } : i);
      }
      return [...prev, {
        product_id: product.id,
        name: product.name,
        price: product.price,
        image_url: product.image_url,
        sku: product.sku,
        gst_rate: product.gst_rate,
        quantity: qty,
      }];
    });
  };
  const remove = (product_id) => setItems((prev) => prev.filter((i) => i.product_id !== product_id));
  const updateQty = (product_id, qty) => setItems((prev) => prev.map((i) => i.product_id === product_id ? { ...i, quantity: Math.max(1, qty) } : i));
  const clear = () => setItems([]);
  const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0);
  const count = items.reduce((s, i) => s + i.quantity, 0);

  return (
    <CartContext.Provider value={{ items, add, remove, updateQty, clear, subtotal, count }}>
      {children}
    </CartContext.Provider>
  );
}
export const useCart = () => useContext(CartContext);
