import { Router } from "express";
import { prisma } from "../lib/prisma";
import { computeStock } from "../lib/stock";

const router = Router();

router.get("/:sku", async (req, res) => {
  const sku = req.params.sku;
  const product = await prisma.product.findUnique({ where: { sku } });
  if (!product) return res.status(404).json({ error: "Unknown SKU" });

  const onHand = product.currentQty !== null
    ? product.currentQty
    : await computeStock(sku);

  res.json({ sku, onHand });
});

export default router;
