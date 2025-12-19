import axios from "axios";

const SALES_BASE = process.env.SALES_API_BASE || "http://127.0.0.1:5000";

export async function notifySalesProduct(product: any) {
  try {
    await axios.post(`${SALES_BASE}/api/inventory-event/`, product, { timeout: 5000 });
  } catch (err: any) {
    console.error("Failed to notify Sales:", err?.message || err);
  }
}
