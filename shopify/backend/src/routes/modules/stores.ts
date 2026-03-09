import { Router } from 'express';
import { prisma } from '../../db.js';
import { requireAuth } from '../../middleware/auth.js';
import { z } from 'zod';

const router = Router();

router.post('/', requireAuth, async (req: any, res) => {
  const schema = z.object({ name: z.string().min(2), subdomain: z.string().regex(/^[a-z0-9-]+$/) });
  const { name, subdomain } = schema.parse(req.body);
  const slug = subdomain;
  const store = await prisma.store.create({ data: { name, slug, subdomain, ownerId: req.user!.id } });
  res.json(store);
});

router.get('/mine', requireAuth, async (req: any, res) => {
  const stores = await prisma.store.findMany({ where: { ownerId: req.user!.id } });
  res.json(stores);
});

router.get('/:subdomain', async (req, res) => {
  const store = await prisma.store.findUnique({ where: { subdomain: req.params.subdomain } });
  if (!store) return res.status(404).json({ error: 'Not found' });
  res.json(store);
});

export default router;
