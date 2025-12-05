// src/services/salesApi.ts
import axios from "axios";

export const SALES_API_BASE = "http://127.0.0.1:5000";

export interface SalesProduct {
  id?: number;
  sku: string;
  name: string;
  unit: string;
  price?: number;
  listPrice?: number;
  stock_qty?: number | null;
  is_active?: boolean;
}

/**
 * Get products from Sales_System (/shop/products/)
 */
export async function getSalesProducts(): Promise<SalesProduct[]> {
  const url = `${SALES_API_BASE}/shop/products/`;
  const res = await axios.get(url);
  return res.data;
}

/**
 * Inventory → Sales
 * Calls Django DRF endpoint /api/sync-from-inventory/
 */
export async function syncInventoryToSales() {
  const url = `${SALES_API_BASE}/api/sync-from-inventory/`;
  const res = await axios.get(url);
  return res.data; // { message, received, updated, ... }
}
