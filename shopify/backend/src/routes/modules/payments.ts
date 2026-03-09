import express, { Router } from 'express';
import Stripe from 'stripe';
import Razorpay from 'razorpay';
import { prisma } from '../../db.js';
import { z } from 'zod';

const router = Router();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY as string, { apiVersion: '2023-10-16' });
const razor = new Razorpay({ key_id: process.env.RAZORPAY_KEY_ID as string, key_secret: process.env.RAZORPAY_KEY_SECRET as string });

router.post('/create-intent', async (req, res) => {
  const schema = z.object({ orderId: z.string(), provider: z.enum(['stripe','razorpay']).default('stripe') });
  const { orderId, provider } = schema.parse(req.body);
  const order = await prisma.order.findUnique({ where: { id: orderId }, include: { store: true } });
  if (!order) return res.status(404).json({ error: 'Order not found' });

  const commissionBps = order.store.commissionBps;
  const commission = Math.floor(order.totalCents * commissionBps / 10000);
  const merchantAmount = order.totalCents - commission;

  if (provider === 'stripe') {
    const pi = await stripe.paymentIntents.create({
      amount: order.totalCents,
      currency: 'usd',
      metadata: { orderId },
      automatic_payment_methods: { enabled: true }
    });
    await prisma.ledgerEntry.createMany({ data: [
      { storeId: order.storeId, orderId: order.id, type: 'CHARGE', amountCents: order.totalCents },
      { storeId: order.storeId, orderId: order.id, type: 'COMMISSION', amountCents: commission }
    ]});
    return res.json({ clientSecret: pi.client_secret });
  } else {
    const ro = await razor.orders.create({ amount: order.totalCents, currency: 'INR', receipt: order.id });
    await prisma.ledgerEntry.createMany({ data: [
      { storeId: order.storeId, orderId: order.id, type: 'CHARGE', amountCents: order.totalCents },
      { storeId: order.storeId, orderId: order.id, type: 'COMMISSION', amountCents: commission }
    ]});
    return res.json({ razorpayOrderId: ro.id, amount: order.totalCents, currency: 'INR' });
  }
});

router.post('/stripe/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature'] as string;
  let event;
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET as string);
  } catch (err: any) {
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  if (event.type === 'payment_intent.succeeded') {
    const pi = event.data.object as Stripe.PaymentIntent;
    const orderId = pi.metadata?.orderId;
    if (orderId) await prisma.order.update({ where: { id: orderId }, data: { status: 'PAID', paymentRef: pi.id } });
  }
  res.json({ received: true });
});

export default router;
