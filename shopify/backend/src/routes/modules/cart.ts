import { Router } from 'express';
import { prisma } from '../../db.js';
import { z } from 'zod';

const router = Router();

router.post('/add', async (req, res) => {
  const schema = z.object({ storeId: z.string(), customerEmail: z.string().email().optional(), productId: z.string(), quantity: z.number().int().positive() });
  const { storeId, customerEmail, productId, quantity } = schema.parse(req.body);

  let customer = customerEmail ? await prisma.customer.findFirst({ where: { email: customerEmail, storeId } }) : null;
  if (!customer && customerEmail) {
    customer = await prisma.customer.create({ data: { email: customerEmail, storeId } });
  }

  let cart = await prisma.cart.findFirst({ where: { storeId, customerId: customer?.id } });
  if (!cart) cart = await prisma.cart.create({ data: { storeId, customerId: customer?.id } });

  const existing = await prisma.cartItem.findFirst({ where: { cartId: cart.id, productId } });
  if (existing) {
    await prisma.cartItem.update({ where: { id: existing.id }, data: { quantity: existing.quantity + quantity } });
  } else {
    await prisma.cartItem.create({ data: { cartId: cart.id, productId, quantity } });
  }
  const items = await prisma.cartItem.findMany({ where: { cartId: cart.id }, include: { product: true } });
  res.json({ cartId: cart.id, items });
});

router.post('/update', async (req, res) => {
  const schema = z.object({ cartId: z.string(), itemId: z.string(), quantity: z.number().int().nonnegative() });
  const { cartId, itemId, quantity } = schema.parse(req.body);
  if (quantity === 0) await prisma.cartItem.delete({ where: { id: itemId } });
  else await prisma.cartItem.update({ where: { id: itemId }, data: { quantity } });
  const items = await prisma.cartItem.findMany({ where: { cartId }, include: { product: true } });
  res.json({ cartId, items });
});

export default router;
