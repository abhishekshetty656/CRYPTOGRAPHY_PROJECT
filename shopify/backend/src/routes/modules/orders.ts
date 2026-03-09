import { Router } from 'express';
import { prisma } from '../../db.js';
import { z } from 'zod';

const router = Router();

router.post('/checkout', async (req, res) => {
  const schema = z.object({
    storeId: z.string(),
    cartId: z.string(),
    email: z.string().email(),
    shipping: z.object({ line1: z.string(), line2: z.string().optional(), city: z.string(), state: z.string(), postalCode: z.string(), country: z.string() }),
    shippingCents: z.number().int().nonnegative(),
  });
  const { storeId, cartId, email, shipping, shippingCents } = schema.parse(req.body);
  const cart = await prisma.cart.findUnique({ where: { id: cartId }, include: { items: { include: { product: true } } } });
  if (!cart || cart.storeId !== storeId) return res.status(400).json({ error: 'Invalid cart' });
  const subtotal = cart.items.reduce((s, i) => s + i.product.priceCents * i.quantity, 0);
  const total = subtotal + shippingCents;
  let customer = await prisma.customer.findFirst({ where: { email, storeId } });
  if (!customer) customer = await prisma.customer.create({ data: { email, storeId } });
  const addr = await prisma.address.create({ data: { customerId: customer.id, ...shipping } });
  const order = await prisma.order.create({ data: {
    storeId, customerId: customer.id, subtotalCents: subtotal, shippingCents, totalCents: total,
    items: { create: cart.items.map(ci => ({ productId: ci.productId, title: ci.product.title, priceCents: ci.product.priceCents, quantity: ci.quantity })) }
  }});
  res.json({ orderId: order.id, totalCents: total });
});

router.get('/store/:storeId', async (req, res) => {
  const orders = await prisma.order.findMany({ where: { storeId: req.params.storeId }, include: { items: true } });
  res.json(orders);
});

router.post('/:orderId/status', async (req, res) => {
  const schema = z.object({ status: z.enum(['PENDING','PAID','FULFILLED','CANCELED','REFUNDED']), shippingTrack: z.string().optional() });
  const data = schema.parse(req.body);
  const order = await prisma.order.update({ where: { id: req.params.orderId }, data });
  res.json(order);
});

export default router;
