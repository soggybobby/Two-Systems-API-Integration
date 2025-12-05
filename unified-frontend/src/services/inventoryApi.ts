// unified-frontend/src/services/inventoryApi.ts
import axios from "axios";

const INVENTORY_API_BASE = "http://localhost:3001";

export type InventoryProduct = {
  sku: string;
  name: string;
  unit: string;
  price?: number;
  listPrice?: number;
  currentQty?: number | null;
};

/**
 * GET all products from Inventory_System (Node)
 * Endpoint: GET /products
 */
export async function getInventoryProducts(): Promise<InventoryProduct[]> {
  const url = `${INVENTORY_API_BASE}/products`;
  const res = await axios.get<InventoryProduct[]>(url);
  return res.data;
}
