import { Router } from 'express';
import { prisma } from '../../db.js';
import { requireAuth } from '../../middleware/auth.js';
import { z } from 'zod';

const router = Router();

router.post('/', requireAuth, async (req: any, res) => {
  const schema = z.object({
    storeId: z.string(),
    title: z.string().min(2),
    description: z.string().min(1),
    priceCents: z.number().int().positive(),
    sku: z.string().min(1),
    inventory: z.number().int().nonnegative(),
    categoryId: z.string().optional(),
    images: z.array(z.string()).default([])
  });
  const data = schema.parse(req.body);
  const slug = data.title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const product = await prisma.product.create({ data: { ...data, slug } });
  res.json(product);
});

router.put('/:id', requireAuth, async (req: any, res) => {
  const id = req.params.id;
  const schema = z.object({ title: z.string().optional(), description: z.string().optional(), priceCents: z.number().int().optional(), sku: z.string().optional(), inventory: z.number().int().optional(), images: z.array(z.string()).optional(), categoryId: z.string().nullable().optional()});
  const data = schema.parse(req.body);
  const product = await prisma.product.update({ where: { id }, data });
  res.json(product);
});

router.delete('/:id', requireAuth, async (req, res) => {
  const id = req.params.id;
  await prisma.product.delete({ where: { id } });
  res.json({ ok: true });
});

router.get('/by-store/:storeId', async (req, res) => {
  const products = await prisma.product.findMany({ where: { storeId: req.params.storeId } });
  res.json(products);
});

export default router;
