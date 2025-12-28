import { Router } from "express";
import { z } from "zod";
import { addLedgerAndBumpCache } from "../lib/stock";
import { prisma } from "../lib/prisma";
import { getIO } from "../ws";

const router = Router();

// sales will POST here after a sale is committed
router.post("/sale-committed", async (req, res) => {
  try {
    const schema = z.object({
      saleId: z.string().min(1),
      items: z.array(
        z.object({
          sku: z.string().min(1),
          qty: z.number().int().positive(),
        })
      ).min(1),
    });

    const payload = schema.parse(req.body);

    const results: any[] = [];

    for (const item of payload.items) {
      // 1) Write ledger + bump cache / update qty
      const r = await addLedgerAndBumpCache({
        sku: item.sku,
        txnType: "SALE",
        qtyChange: -item.qty,
        refType: "SALE",
        refId: payload.saleId,
        note: "Sale committed",
      });

      // 2) Read updated product qty
      const updated = await prisma.product.findUnique({
        where: { sku: item.sku },
        select: { sku: true, currentQty: true, updatedAt: true },
      });

      // 3) Emit websocket event to all connected clients
      // Guard: if WS isn't initialized, don't crash the request
      try {
        const io = getIO();
        io.emit("stock:update", {
          sku: item.sku,
          currentQty: updated?.currentQty ?? 0,
          refType: "SALE",
          refId: payload.saleId,
        });
      } catch (e) {
        // WS not initialized or unavailable; ignore for API reliability
      }

      results.push({
        ...r,
        sku: item.sku,
        currentQty: updated?.currentQty ?? null,
      });
    }

    return res.json({
      ok: true,
      saleId: payload.saleId,
      count: results.length,
      items: results,
    });
  } catch (err: any) {
    // Zod parse errors or runtime errors
    return res.status(400).json({
      ok: false,
      error: err?.message ?? "Bad request",
    });
  }
});

export default router;
