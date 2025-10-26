import { Router } from "express";
import { prisma } from "../lib/prisma";
import { computeStock } from "../lib/stock";

const router = Router();

// ✅ Check current stock for a product
router.get("/:sku", async (req, res) => {
  const sku = req.params.sku;

  const product = await prisma.product.findUnique({ where: { sku } });
  if (!product) return res.status(404).json({ error: "Unknown SKU" });

  const onHand =
    product.currentQty !== null ? product.currentQty : await computeStock(sku);

  res.json({ sku, onHand });
});

// ✅ Update stock after a sale
router.post("/update", async (req, res) => {
  const { sku, qty } = req.body;

  if (!sku || typeof qty !== "number") {
    return res.status(400).json({ error: "Invalid input" });
  }

  const product = await prisma.product.findUnique({ where: { sku } });
  if (!product) {
    return res.status(404).json({ error: "Unknown SKU" });
  }

  // Use currentQty if set, otherwise compute dynamically
  const onHand =
    product.currentQty !== null ? product.currentQty : await computeStock(sku);

  if (onHand < qty) {
    return res.status(400).json({ error: "Not enough stock", sku, onHand });
  }

  // Deduct stock
  const updated = await prisma.product.update({
    where: { sku },
    data: { currentQty: onHand - qty },
  });

  res.json({
    success: true,
    message: "Stock updated",
    sku: updated.sku,
    remaining: updated.currentQty,
  });
});

export default router;
