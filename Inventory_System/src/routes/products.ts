import { Router } from "express";
import { prisma } from "../lib/prisma";
import { getIO } from "../ws";

const router = Router();

/**
 * GET /products
 * Returns all products
 */
router.get("/", async (_req, res) => {
  const items = await prisma.product.findMany({
    orderBy: { updatedAt: "desc" },
  });
  res.json(items);
});

/**
 * GET /products/:sku
 * Returns a single product by SKU for Sales to fetch on WS notify
 */
router.get("/:sku", async (req, res) => {
  const sku = req.params.sku.trim();
  const product = await prisma.product.findUnique({ where: { sku } });

  if (!product) return res.status(404).json({ detail: "Not found" });

  res.json({
    sku: product.sku,
    name: product.name,
    description: product.description ?? "",
    unit: product.unit ?? "pcs",
    listPrice: product.listPrice ? Number(product.listPrice) : 0,
    salePriceOverride: product.salePriceOverride ? Number(product.salePriceOverride) : null,
    publishedToShop: product.publishedToShop,
    status: product.status,
    currentQty: product.currentQty ?? 0,
    updatedAt: product.updatedAt,
  });
});

/**
 * POST /products
 * Create product + emit WS event
 */
router.post("/", async (req, res) => {
  const data = req.body;

  const product = await prisma.product.create({
    data: {
      sku: data.sku,
      name: data.name,
      description: data.description ?? "",
      unit: data.unit ?? "pcs",
      listPrice: data.listPrice ?? null,
      publishedToShop: data.publishedToShop ?? false,
      salePriceOverride: data.salePriceOverride ?? null,
      status: data.status ?? "ACTIVE",
      currentQty: data.currentQty ?? 0,
    },
  });

  res.status(201).json(product);

  try {
    getIO().emit("products:changed", {
      sku: product.sku,
      action: "created",
      updatedAt: product.updatedAt,
    });
  } catch {}
});

/**
 * PATCH /products/:sku
 * Update product + emit WS event
 */
router.patch("/:sku", async (req, res) => {
  const sku = req.params.sku.trim();
  const data = req.body;

  const updated = await prisma.product.update({
    where: { sku },
    data: {
      name: data.name,
      description: data.description,
      unit: data.unit,
      listPrice: data.listPrice,
      publishedToShop: data.publishedToShop,
      salePriceOverride: data.salePriceOverride,
      status: data.status,
      currentQty: data.currentQty,
    },
  });

  res.json(updated);

  try {
    getIO().emit("products:changed", {
      sku: updated.sku,
      action: "updated",
      updatedAt: updated.updatedAt,
    });
  } catch {}
});

/**
 * DELETE /products/:sku
 * Delete product + emit WS event
 */
router.delete("/:sku", async (req, res) => {
  const sku = req.params.sku.trim();

  try {
    const deleted = await prisma.product.delete({ where: { sku } });
    res.json({ ok: true, sku: deleted.sku });

    try {
      getIO().emit("products:changed", {
        sku: deleted.sku,
        action: "deleted",
        updatedAt: new Date(),
      });
    } catch {}
  } catch (err: any) {
    if (err?.code === "P2025") {
      return res.status(404).json({ detail: "Not found" });
    }
    return res.status(500).json({ detail: "Delete failed" });
  }
});

export default router;
