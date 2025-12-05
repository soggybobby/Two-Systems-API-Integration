// src/App.tsx
import { useState } from "react";
import "./App.css";

import {
  getInventoryProducts,
  syncSalesToInventory,
} from "./services/inventoryApi";
import {
  getSalesProducts,
  syncInventoryToSales,
} from "./services/salesApi";

// Use `import type` so TS knows these are types only
import type { InventoryProduct } from "./services/inventoryApi";
import type { SalesProduct } from "./services/salesApi";

function App() {
  const [inventory, setInventory] = useState<InventoryProduct[]>([]);
  const [sales, setSales] = useState<SalesProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState("");

  // helper: pick a price from either price or listPrice
  const getPrice = (p: { price?: number; listPrice?: number }) =>
    p.price ?? p.listPrice ?? 0;

  // ---- button actions ----
  const loadInventory = async () => {
    setLoading(true);
    setLog("");
    try {
      const data = await getInventoryProducts();
      setInventory(data);
      setLog("✅ Loaded Inventory products");
    } catch (err) {
      console.error(err);
      setLog("❌ Error loading inventory");
    }
    setLoading(false);
  };

  const loadSales = async () => {
    setLoading(true);
    setLog("");
    try {
      const data = await getSalesProducts();
      setSales(data);
      setLog("✅ Loaded Sales products");
    } catch (err) {
      console.error(err);
      setLog("❌ Error loading sales");
    }
    setLoading(false);
  };

  const doPullInventoryToSales = async () => {
    setLoading(true);
    setLog("");
    try {
      const res = await syncInventoryToSales();
      setLog(`✅ Pull Inventory → Sales: ${res.message || ""}`);
    } catch (err) {
      console.error(err);
      setLog("❌ Error pulling Inventory → Sales");
    }
    setLoading(false);
  };

  const doPushSalesToInventory = async () => {
    setLoading(true);
    setLog("");
    try {
      const res = await syncSalesToInventory();
      setLog(`✅ Push Sales → Inventory: ${res.message || ""}`);
    } catch (err) {
      console.error(err);
      setLog("❌ Error pushing Sales → Inventory");
    }
    setLoading(false);
  };

    return (
    <div className="app-root">
      <header className="app-header">
        <h1>Two-Systems Integration Dashboard</h1>

        <div className="button-row">
          <button
            className="btn"
            onClick={loadInventory}
            disabled={loading}
          >
            Load Inventory products (Node)
          </button>
          <button
            className="btn"
            onClick={loadSales}
            disabled={loading}
          >
            Load Sales products (Django)
          </button>
          <button
            className="btn btn-accent"
            onClick={doPullInventoryToSales}
            disabled={loading}
          >
            Pull Inventory → Sales
          </button>
          <button
            className="btn btn-accent"
            onClick={doPushSalesToInventory}
            disabled={loading}
          >
            Push Sales → Inventory
          </button>
        </div>

        <div className="status-bar">
          {loading ? <span>⏳ Working…</span> : log && <span>{log}</span>}
        </div>
      </header>

      {/* main centered layout */}
      <main className="app-main">
        <div className="tables-row">
          {/* LEFT: Inventory */}
          <section className="panel">
            <div className="panel-header">
              <h2>Inventory products (Node @ :3001)</h2>
              <span className="panel-count">
                {inventory.length} items
              </span>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Name</th>
                    <th>Unit</th>
                    <th className="num">Price</th>
                    <th className="num">Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.map((p) => (
                    <tr key={p.sku}>
                      <td>{p.sku}</td>
                      <td>{p.name}</td>
                      <td>{p.unit}</td>
                      <td className="num">{getPrice(p)}</td>
                      <td className="num">{p.currentQty ?? 0}</td>
                    </tr>
                  ))}
                  {inventory.length === 0 && (
                    <tr>
                      <td colSpan={5} className="empty">
                        No inventory loaded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* RIGHT: Sales */}
          <section className="panel">
            <div className="panel-header">
              <h2>Sales products (Django @ :5000)</h2>
              <span className="panel-count">
                {sales.length} items
              </span>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Name</th>
                    <th>Unit</th>
                    <th className="num">Price</th>
                    <th className="num">Stock</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map((p) => (
                    <tr key={p.sku}>
                      <td>{p.sku}</td>
                      <td>{p.name}</td>
                      <td>{p.unit}</td>
                      <td className="num">{p.price}</td>
                      <td className="num">{p.stock_qty ?? "-"}</td>
                    </tr>
                  ))}
                  {sales.length === 0 && (
                    <tr>
                      <td colSpan={5} className="empty">
                        No sales products loaded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}


export default App;
