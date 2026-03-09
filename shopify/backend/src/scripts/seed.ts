import { prisma } from '../db.js';

async function main(){
  const plans = [
    { name: 'Basic', priceCents: 1900, interval: 'month', features: ['100 products', 'Basic analytics'] },
    { name: 'Professional', priceCents: 4900, interval: 'month', features: ['1000 products', 'Advanced analytics', 'Custom domain'] },
    { name: 'Enterprise', priceCents: 9900, interval: 'month', features: ['Unlimited', 'Priority support', 'SLA'] },
  ];
  for (const p of plans) {
    await prisma.subscriptionPlan.upsert({ where: { name: p.name }, create: p, update: p });
  }
  console.log('Seeded plans');
}

main().finally(() => prisma.$disconnect());
