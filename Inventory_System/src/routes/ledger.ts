import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";
import { addLedgerAndBumpCache } from "../lib/stock";

const router = Router();

/**
 * GET /ledger
 * Returns recent ledger rows for the dashboard
 */
router.get("/", async (_req, res) => {
  const rows = await prisma.inventoryLedger.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
    select: {
      id: true,
      sku: true,
      txnType: true,
      qtyChange: true,
      refType: true,
      refId: true,
      note: true,
      createdAt: true,
    },
  });

  res.json(rows);
});

router.post("/", async (req, res) => {
  const schema = z.object({
    sku: z.string().min(1),
    txnType: z.enum(["PUR","SALE","ADJ+","ADJ-","RTN_IN","RTN_OUT","XFER_IN","XFER_OUT"]),
    qtyChange: z.number().int(),
    refType: z.string().optional(),
    refId: z.string().optional(),
    note: z.string().optional()
  });

  const data = schema.parse(req.body);

  // simple guard: SALE/ADJ-/RTN_OUT/XFER_OUT must be negative
  if (
    (data.txnType === "SALE" ||
      data.txnType === "ADJ-" ||
      data.txnType === "RTN_OUT" ||
      data.txnType === "XFER_OUT") &&
    data.qtyChange > 0
  ) {
    data.qtyChange = -Math.abs(data.qtyChange);
  }

  const created = await addLedgerAndBumpCache(data);
  res.status(201).json(created);
});

export default router;
