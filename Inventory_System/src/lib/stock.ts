import { prisma } from "./prisma";
import type { Prisma } from "@prisma/client";

export async function computeStock(sku: string): Promise<number> {
  const agg = await prisma.inventoryLedger.aggregate({
    where: { sku },
    _sum: { qtyChange: true },
  });
  return agg._sum.qtyChange ?? 0;
}

export async function addLedgerAndBumpCache(input: {
  sku: string;
  txnType: string;
  qtyChange: number;
  refType?: string;
  refId?: string;
  note?: string;
}) {
  return prisma.$transaction(async (tx: Prisma.TransactionClient) => {
    const product = await tx.product.findUnique({ where: { sku: input.sku } });
    if (!product) throw new Error("Unknown SKU");

    const ledger = await tx.inventoryLedger.create({ data: input });

    if (product.currentQty !== null) {
      await tx.product.update({
        where: { sku: input.sku },
        data: { currentQty: (product.currentQty ?? 0) + input.qtyChange },
      });
    }
    return ledger;
  });
}
