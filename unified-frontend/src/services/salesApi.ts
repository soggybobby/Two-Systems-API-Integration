// unified-frontend/src/services/salesApi.ts
import axios from "axios";

const SALES_API_BASE = "http://localhost:5000";

export type SalesProduct = {
  sku: string;
  name: string;
  unit: string;
  price: number;
  stock_qty?: number | null;
};

/**
 * GET active products from Django (used by dashboard)
 * Endpoint: GET /products/
 */
export async function getSalesProducts(): Promise<SalesProduct[]> {
  const url = `${SALES_API_BASE}/products/`;
  const res = await axios.get<SalesProduct[]>(url);
  return res.data;
}

/**
 * Inventory → Sales
 * Django endpoint: GET /api/sync-from-inventory/
 */
export async function syncInventoryToSales(): Promise<any> {
  const url = `${SALES_API_BASE}/api/sync-from-inventory/`;
  const res = await axios.get(url);
  return res.data;
}

/**
 * Sales → Inventory
 * Django endpoint: POST /api/sync-to-inventory/
 * Django will then POST to Node /products/sync-from-sales.
 */
export async function syncSalesToInventory(): Promise<any> {
  const url = `${SALES_API_BASE}/api/sync-to-inventory/`;
  const res = await axios.post(url); // no body needed
  return res.data;
}
