import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";
import axios from "axios";

const router = Router();

/** Django Sales_System base (keep /shop) */
const SALES_SYSTEM_API = "http://127.0.0.1:5000/shop";

/* ------------------------- Helpers / Schemas ------------------------- */

/** Convert string/number to number safely */
const toNumber = (v: unknown, fallback = 0): number => {
  const n =
    typeof v === "string"
      ? Number(v)
      : typeof v === "number"
      ? v
      : NaN;
  return Number.isFinite(n) ? n : fallback;
};

/**
 * Shape we expect from Sales_System when it POSTs to us
 * via /products/sync-from-sales
 */
const SalesProductSchema = z.object({
  sku: z.string().min(1),
  name: z.string().min(1),
  description: z.string().nullable().optional(),
  unit: z.string().min(1).optional(),                 // default to "pcs" below
  price: z.union([z.number(), z.string()]).optional(), // Django Decimal might be string
  stock_qty: z.union([z.number().int(), z.string()]).optional(),
});
const SalesProductArraySchema = z.array(SalesProductSchema);

/* ------------------------------- Routes ------------------------------ */

/** Get all products from our local Prisma DB */
router.get("/", async (_req, res) => {
  const products = await prisma.product.findMany({
    orderBy: { updatedAt: "desc" },
  });
  res.json(products);
});

/**
 * Inventory ← Sales
 * Receiver endpoint for Sales_System to push products here.
 * Django sends {sku, name, unit, price, stock_qty}.
 * We store them as listPrice + currentQty in Prisma.
 */
router.post("/sync-from-sales", async (req, res) => {
  try {
    const parsed = SalesProductArraySchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({
        error: "Invalid payload format",
        details: parsed.error.flatten(),
      });
    }

    const products = parsed.data;

    for (const p of products) {
      await prisma.product.upsert({
        where: { sku: p.sku },
        update: {
          name: p.name,
          description: p.description ?? "",
          unit: p.unit ?? "pcs",
          listPrice: toNumber(p.price, 0),        // 👈 use price
          currentQty: toNumber(p.stock_qty, 0),   // 👈 use stock_qty
        },
        create: {
          sku: p.sku,
          name: p.name,
          description: p.description ?? "",
          unit: p.unit ?? "pcs",
          listPrice: toNumber(p.price, 0),
          currentQty: toNumber(p.stock_qty, 0),
        },
      });
    }

    return res.json({
      message: "Products received successfully from Sales_System",
      count: products.length,
    });
  } catch (err: any) {
    console.error("Error saving products from Sales_System:", err?.message || err);
    return res.status(500).json({ error: err?.message || "Server error" });
  }
});

/**
 * Inventory → Sales
 * Pull products from Django and upsert locally (used by /products/sync)
 */
router.get("/sync", async (_req, res) => {
  try {
    const response = await axios.get(`${SALES_SYSTEM_API}/products/`);
    const products = response.data as any[];

    for (const p of products) {
      await prisma.product.upsert({
        where: { sku: p.sku },
        update: {
          name: p.name,
          description: p.description || "",
          unit: p.unit || "pcs",
          listPrice: toNumber(p.price, 0),
          // we do not touch currentQty here (Inventory is source of truth)
        },
        create: {
          sku: p.sku,
          name: p.name,
          description: p.description || "",
          unit: p.unit || "pcs",
          listPrice: toNumber(p.price, 0),
          currentQty: 0,
        },
      });
    }

    res.status(200).json({
      message: "Products synced successfully from Sales_System",
      count: products.length,
      data: products,
    });
  } catch (error: any) {
    console.error("Error syncing products:", error?.message || error);
    res.status(500).json({
      message: "Failed to fetch products from Sales_System",
      error: error?.message || "Request failed",
    });
  }
});

/** Manually add a new product to local DB */
router.post("/", async (req, res) => {
  const schema = z.object({
    sku: z.string().min(1),
    name: z.string().min(1),
    description: z.string().optional(),
    unit: z.string().min(1),
    listPrice: z.coerce.number().nonnegative().optional(),
    useQtyCache: z.boolean().optional(),
  });
  const data = schema.parse(req.body);

  const product = await prisma.product.create({
    data: {
      sku: data.sku,
      name: data.name,
      description: data.description,
      unit: data.unit,
      listPrice: data.listPrice,
      currentQty: data.useQtyCache ? 0 : null,
    },
  });
  res.status(201).json(product);
});

/** Get single product by SKU */
router.get("/:sku", async (req, res) => {
  const product = await prisma.product.findUnique({
    where: { sku: req.params.sku },
  });
  if (!product) return res.status(404).json({ error: "Not found" });
  res.json(product);
});

export default router;
