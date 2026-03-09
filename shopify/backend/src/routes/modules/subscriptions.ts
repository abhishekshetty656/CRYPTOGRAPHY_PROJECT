import { Router } from 'express';
import { prisma } from '../../db.js';
import { z } from 'zod';

const router = Router();

router.get('/plans', async (_req, res) => {
  const plans = await prisma.subscriptionPlan.findMany();
  res.json(plans);
});

router.post('/assign', async (req, res) => {
  const schema = z.object({ storeId: z.string(), planId: z.string(), periodEnd: z.string() });
  const { storeId, planId, periodEnd } = schema.parse(req.body);
  const sub = await prisma.subscription.upsert({
    where: { storeId },
    create: { storeId, planId, provider: 'stripe', currentPeriodEnd: new Date(periodEnd) },
    update: { planId, currentPeriodEnd: new Date(periodEnd), status: 'ACTIVE' }
  });
  res.json(sub);
});

export default router;
