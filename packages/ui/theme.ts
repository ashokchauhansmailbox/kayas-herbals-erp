/**
 * Kaya's Herbals — Brand Tokens (single source of truth)
 * Consumed by all three apps (web-store, admin, seller-portal).
 * Change here → rebrand everywhere.
 */
export const colors = {
  greenPrimary: "#1F3D2B",
  greenSoft: "#4C8B5A",
  offwhite: "#F8F5EE",
  gold: "#C9A24B",
  text: "#2D2D2D",
  border: "#E5E1D8",
  danger: "#A43026",
  warning: "#D4A373",
  success: "#365E32",
};

export const fonts = {
  heading: '"Poppins", system-ui, sans-serif',
  body: '"Inter", system-ui, sans-serif',
  mono: '"JetBrains Mono", ui-monospace, monospace',
};

export const radius = { sm: "4px", md: "8px", lg: "12px", xl: "20px" };

export const spacing = {
  container: "max-w-7xl mx-auto px-6 lg:px-10",
};

export const kpiKeys = [
  "sales", "revenue", "orders",
  "low_stock", "near_expiry",
  "outstanding_payments", "top_products",
];

export const stockStates = ["available", "reserved", "damaged", "returned", "expired"];
