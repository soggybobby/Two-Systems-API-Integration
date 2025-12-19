// Inventory_System/src/routes/products.ts
import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";

const router = Router();

// All products (admin/internal)
router.get("/", async (_req, res) => {
  const products = await prisma.product.findMany({ orderBy: { updatedAt: "desc" } });
  res.json(products);
});

// Public products for Sales storefront (only published + active)
router.get("/public", async (_req, res) => {
  const products = await prisma.product.findMany({
    where: {
      status: "ACTIVE",
      publishedToShop: true,
    },
    orderBy: { updatedAt: "desc" },
  });

  const data = products.map((p) => ({
    sku: p.sku,
    name: p.name,
    description: p.description,
    unit: p.unit,
    listPrice: p.listPrice ? Number(p.listPrice) : 0,
    salePriceOverride: p.salePriceOverride ? Number(p.salePriceOverride) : null,
    effectivePrice: p.salePriceOverride ? Number(p.salePriceOverride) : (p.listPrice ? Number(p.listPrice) : 0),
    currentQty: p.currentQty ?? 0,
    publishedToShop: p.publishedToShop,
    status: p.status,
    updatedAt: p.updatedAt,
  }));

  res.json(data);
});

// Create product (admin/internal)
router.post("/", async (req, res) => {
  const schema = z.object({
    sku: z.string().min(1),
    name: z.string().min(1),
    description: z.string().optional(),
    unit: z.string().min(1),
    listPrice: z.coerce.number().nonnegative().optional(),
    currentQty: z.coerce.number().int().optional(),
    publishedToShop: z.boolean().optional(),
    salePriceOverride: z.coerce.number().nonnegative().nullable().optional(),
  });

  const data = schema.parse(req.body);

  const product = await prisma.product.create({
    data: {
      sku: data.sku.trim().toUpperCase(),
      name: data.name,
      description: data.description ?? null,
      unit: data.unit,
      listPrice: data.listPrice ?? 0,
      currentQty: data.currentQty ?? 0,
      publishedToShop: data.publishedToShop ?? false,
      salePriceOverride: data.salePriceOverride ?? null,
      status: "ACTIVE",
    },
  });

  res.status(201).json(product);
});

// Update product (admin/internal)
router.patch("/:sku", async (req, res) => {
  const sku = req.params.sku.trim().toUpperCase();

  const schema = z.object({
    name: z.string().optional(),
    description: z.string().nullable().optional(),
    unit: z.string().optional(),
    listPrice: z.coerce.number().nonnegative().optional(),
    currentQty: z.coerce.number().int().optional(),
    publishedToShop: z.boolean().optional(),
    salePriceOverride: z.coerce.number().nonnegative().nullable().optional(),
    status: z.string().optional(),
  });

  const data = schema.parse(req.body);

  const updated = await prisma.product.update({
    where: { sku },
    data: {
      ...data,
    },
  });

  res.json(updated);
});

export default router;
