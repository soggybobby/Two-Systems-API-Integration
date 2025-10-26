import { Router } from 'express';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const router = Router();

// POST /api/v1/stock-adjustments
router.post('/stock-adjustments', async (req, res) => {
  const { idempotencyKey, sku, delta, reason, reference } = req.body || {};

  // 1) Validate input
  if (!idempotencyKey || !sku || !Number.isInteger(delta)) {
    return res.status(400).json({ error: 'invalid payload', code: 'VALIDATION_ERROR' });
  }

  try {
    // 2) One DB transaction for safety
    const result = await prisma.$transaction(async (tx) => {
      // Idempotency check (assumes InventoryLedger.idempotencyKey is UNIQUE)
      const dup = await tx.inventoryLedger.findUnique({ where: { idempotencyKey } }).catch(() => null);
      if (dup) return { duplicate: true };

      const prod = await tx.product.findUnique({ where: { sku } });
      if (!prod) {
        const e: any = new Error('SKU_NOT_FOUND');
        e.http = 404;
        throw e;
      }

      const newQty = (prod.currentQty ?? 0) + delta;
      if (newQty < 0) {
        const e: any = new Error('INSUFFICIENT_STOCK');
        e.http = 422;
        throw e;
      }

      await tx.inventoryLedger.create({
        data: {
          idempotencyKey,
          sku,
          txnType: reason || 'SALE',
          qtyChange: delta,
          refType: 'SALE',
          refId: reference || null
        }
      });

      await tx.product.update({
        where: { sku },
        data: { currentQty: newQty }
      });

      return { sku, qty: newQty };
    });

    if ((result as any).duplicate) {
      return res.status(409).json({ error: 'duplicate idempotency key', code: 'DUPLICATE' });
    }
    return res.status(201).json(result);
  } catch (e: any) {
    if (e.http === 404) return res.status(404).json({ error: 'sku not found', code: 'SKU_NOT_FOUND' });
    if (e.http === 422) return res.status(422).json({ error: 'insufficient stock', code: 'INSUFFICIENT_STOCK' });
    console.error(e);
    return res.status(500).json({ error: 'server error', code: 'SERVER_ERROR' });
  }
});

export default router;
