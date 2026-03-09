import { Router } from 'express';
import { prisma } from '../../db.js';
import { requireAuth, requireRole } from '../../middleware/auth.js';

const router = Router();

router.use(requireAuth, requireRole(['ADMIN']));

router.get('/stats', async (_req, res) => {
  const stores = await prisma.store.count();
  const users = await prisma.user.count();
  const revenue = await prisma.ledgerEntry.aggregate({ _sum: { amountCents: true }, where: { type: 'COMMISSION' } });
  res.json({ stores, users, platformRevenueCents: revenue._sum.amountCents || 0 });
});

router.post('/commission', async (req, res) => {
  const percent = Number(req.body.percent);
  await prisma.store.updateMany({ data: { commissionBps: Math.floor(percent * 100) } });
  res.json({ ok: true });
});

router.post('/suspend/:storeId', async (req, res) => {
  await prisma.store.update({ where: { id: req.params.storeId }, data: { isSuspended: true } });
  res.json({ ok: true });
});

export default router;
