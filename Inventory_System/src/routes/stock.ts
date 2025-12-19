import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";

const router = Router();

const AdjustSchema = z.object({
  refType: z.string().default("SALE"),
  refId: z.string().min(1),
  items: z.array(
    z.object({
      sku: z.string().min(1),
      qty: z.coerce.number().int().positive(),
    })
  ),
});

/**
 * POST /stock/adjust
 * body:
 * {
 *   "refType": "SALE",
 *   "refId": "S-00001",
 *   "items": [{"sku":"ABC-01","qty":2}]
 * }
 *
 * Behavior:
 * - subtract qty from Product.currentQty
 * - create InventoryLedger row per item (SALE_OUT)
 */
router.post("/adjust", async (req, res) => {
  const parsed = AdjustSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid payload", details: parsed.error.flatten() });
  }

  const { refType, refId, items } = parsed.data;

  try {
    const results: any[] = [];

    for (const it of items) {
      const sku = it.sku.trim().toUpperCase();
      const qty = it.qty;

      const product = await prisma.product.findUnique({ where: { sku } });
      if (!product) {
        results.push({ sku, ok: false, reason: "NOT_FOUND" });
        continue;
      }

      const current = product.currentQty ?? 0;
      const newQty = current - qty;

      if (newQty < 0) {
        results.push({ sku, ok: false, reason: "INSUFFICIENT_STOCK", currentQty: current });
        continue;
      }

      await prisma.$transaction(async (tx) => {
        await tx.product.update({
          where: { sku },
          data: { currentQty: newQty },
        });

        await tx.inventoryLedger.create({
          data: {
            sku,
            txnType: "SALE_OUT",
            qtyChange: -qty,
            refType,
            refId,
            note: "Stock deducted from Sales checkout",
          },
        });
      });

      results.push({ sku, ok: true, before: current, after: newQty, deducted: qty });
    }

    return res.json({ message: "Stock adjusted", refType, refId, results });
  } catch (e: any) {
    console.error(e);
    return res.status(500).json({ error: e?.message || "Server error" });
  }
});

export default router;
