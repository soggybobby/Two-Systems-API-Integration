import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";
import axios from "axios";

const router = Router();

// Django Sales_System API base URL
const SALES_SYSTEM_API = "http://127.0.0.1:5000/shop";

// 🟢 Get all products (from local DB)
router.get("/", async (_req, res) => {
  const products = await prisma.product.findMany({ orderBy: { updatedAt: "desc" } });
  res.json(products);
});

// 🟢 Fetch products directly from Django API
router.get("/sync", async (_req, res) => {
  try {
    const response = await axios.get(`${SALES_SYSTEM_API}/products/`);
    const products = response.data;

    // Optionally store/update products in your Prisma DB
    for (const p of products) {
      await prisma.product.upsert({
        where: { sku: p.sku },
        update: {
          name: p.name,
          description: p.description || "",
          unit: p.unit || "pcs",
          listPrice: p.price || 0,
        },
        create: {
          sku: p.sku,
          name: p.name,
          description: p.description || "",
          unit: p.unit || "pcs",
          listPrice: p.price || 0,
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
    console.error("Error syncing products:", error.message);
    res.status(500).json({
      message: "Failed to fetch products from Sales_System",
      error: error.message,
    });
  }
});

// 🟢 Add a new product manually (local DB)
router.post("/", async (req, res) => {
  const schema = z.object({
    sku: z.string().min(1),
    name: z.string().min(1),
    description: z.string().optional(),
    unit: z.string().min(1),
    listPrice: z.coerce.number().nonnegative().optional(),
    useQtyCache: z.boolean().optional(), // set true if you want currentQty
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

// 🟢 Get single product by SKU
router.get("/:sku", async (req, res) => {
  const product = await prisma.product.findUnique({ where: { sku: req.params.sku } });
  if (!product) return res.status(404).json({ error: "Not found" });
  res.json(product);
});

export default router;
