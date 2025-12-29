import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";
import { getIO } from "../ws";

const router = Router();

/**
 * GET /ledger
 * Returns latest ledger entries (for dashboard)
 */
router.get("/", async (_req, res) => {
  const rows = await prisma.inventoryLedger.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
  });
  res.json(rows);
});

const LedgerSchema = z.object({
  sku: z.string().min(1),
  txnType: z.enum([
    "PUR",
    "SALE",
    "ADJ+",
    "ADJ-",
    "RTN_IN",
    "RTN_OUT",
    "XFER_IN",
    "XFER_OUT",
  ]),
  qtyChange: z.number().int(),
  refType: z.string().optional(),
  refId: z.string().optional(),
  note: z.string().optional(),
});

/**
 * POST /ledger
 * Manual ledger entry that ALSO updates stock
 */
router.post("/", async (req, res) => {
  const data = LedgerSchema.parse(req.body);
  const sku = data.sku.trim().toUpperCase();

  // normalize qty sign
  const outflow = new Set(["SALE", "ADJ-", "RTN_OUT", "XFER_OUT"]);
  const inflow = new Set(["PUR", "ADJ+", "RTN_IN", "XFER_IN"]);

  if (outflow.has(data.txnType) && data.qtyChange > 0) {
    data.qtyChange = -Math.abs(data.qtyChange);
  }
  if (inflow.has(data.txnType) && data.qtyChange < 0) {
    data.qtyChange = Math.abs(data.qtyChange);
  }

  try {
    const result = await prisma.$transaction(async (tx) => {
      const product = await tx.product.findUnique({ where: { sku } });
      if (!product) return { ok: false, reason: "NOT_FOUND" as const };

      const before = product.currentQty ?? 0;
      const after = before + data.qtyChange;

      if (after < 0) {
        return {
          ok: false,
          reason: "INSUFFICIENT_STOCK" as const,
          currentQty: before,
        };
      }

      await tx.product.update({
        where: { sku },
        data: { currentQty: after },
      });

      const ledger = await tx.inventoryLedger.create({
        data: {
          sku,
          txnType: data.txnType,
          qtyChange: data.qtyChange,
          refType: data.refType,
          refId: data.refId,
          note: data.note,
        },
      });

      return { ok: true, before, after, ledger };
    });

    if (!result.ok) {
      if (result.reason === "NOT_FOUND") {
        return res.status(404).json({ detail: "Product not found", sku });
      }
      return res.status(400).json({
        detail: "Insufficient stock",
        sku,
        currentQty: result.currentQty,
      });
    }

    /* 🔥 IMPORTANT WEBSOCKET EMITS 🔥 */
    try {
      const io = getIO();

      // for dashboards / logs
      io.emit("ledger:created", {
        sku,
        txnType: data.txnType,
        qtyChange: data.qtyChange,
      });

      // for anyone tracking stock
      io.emit("stock:changed", {
        sku,
        currentQty: result.after,
      });

      // 🔑 THIS IS WHAT MAKES SALES UPDATE
      io.emit("products:changed", {
        sku,
        action: "updated",
        updatedAt: new Date(),
      });
    } catch {}

    return res.status(201).json(result);
  } catch (e: any) {
    console.error(e);
    return res.status(500).json({ detail: e?.message || "Server error" });
  }
});

export default router;
