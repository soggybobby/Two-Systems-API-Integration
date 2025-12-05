// src/services/inventoryApi.ts
import axios from "axios";

export const INVENTORY_API_BASE = "http://localhost:3001";

export interface InventoryProduct {
  id?: number;
  sku: string;
  name: string;
  unit: string;
  // Node API usually returns price, but we keep listPrice optional too
  price?: number;
  listPrice?: number;
  status?: string;
  currentQty?: number | null;
}

/**
 * Get products from Inventory_System
 */
export async function getInventoryProducts(): Promise<InventoryProduct[]> {
  const url = `${INVENTORY_API_BASE}/products`;
  const res = await axios.get(url);
  return res.data;
}

/**
 * Sales → Inventory
 * Uses existing GET /products/sync (which pulls from Django /shop/products/)
 */
export async function syncSalesToInventory() {
  const url = `${INVENTORY_API_BASE}/products/sync`;
  const res = await axios.get(url);
  return res.data; // { message, count, data: [...] }
}
