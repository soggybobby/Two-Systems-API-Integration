import { Router } from "express";
import { z } from "zod";
import { prisma } from "../lib/prisma";

const router = Router();

router.get("/", async (_req, res) => {
  const products = await prisma.product.findMany({ orderBy: { updatedAt: "desc" } });
  res.json(products);
});

router.post("/", async (req, res) => {
  const schema = z.object({
    sku: z.string().min(1),
    name: z.string().min(1),
    description: z.string().optional(),
    unit: z.string().min(1),
    listPrice: z.coerce.number().nonnegative().optional(),
    useQtyCache: z.boolean().optional() // set true if you want currentQty
  });
  const data = schema.parse(req.body);

  const product = await prisma.product.create({
    data: {
      sku: data.sku,
      name: data.name,
      description: data.description,
      unit: data.unit,
      listPrice: data.listPrice,
      currentQty: data.useQtyCache ? 0 : null
    }
  });
  res.status(201).json(product);
});

router.get("/:sku", async (req, res) => {
  const product = await prisma.product.findUnique({ where: { sku: req.params.sku } });
  if (!product) return res.status(404).json({ error: "Not found" });
  res.json(product);
});

export default router;
