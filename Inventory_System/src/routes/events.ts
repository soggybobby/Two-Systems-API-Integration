import { Router } from "express";
import { z } from "zod";
import { addLedgerAndBumpCache } from "../lib/stock";

const router = Router();

// sales will POST here after a sale is committed
router.post("/sale-committed", async (req, res) => {
  const schema = z.object({
    saleId: z.string(),
    items: z.array(z.object({ sku: z.string(), qty: z.number().int().positive() }))
  });
  const payload = schema.parse(req.body);

  // write one ledger row per item, idempotency can use unique(refType, refId, sku)
  const results = [];
  for (const item of payload.items) {
    const r = await addLedgerAndBumpCache({
      sku: item.sku,
      txnType: "SALE",
      qtyChange: -item.qty,
      refType: "SALE",
      refId: payload.saleId,
      note: "Sale committed"
    });
    results.push(r);
  }
  res.json({ ok: true, count: results.length });
});

export default router;
