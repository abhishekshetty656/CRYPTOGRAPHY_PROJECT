import { Router } from 'express';
import auth from './modules/auth.js';
import stores from './modules/stores.js';
import products from './modules/products.js';
import cart from './modules/cart.js';
import orders from './modules/orders.js';
import payments from './modules/payments.js';
import subscriptions from './modules/subscriptions.js';
import admin from './modules/admin.js';

export const router = Router();
router.use('/auth', auth);
router.use('/stores', stores);
router.use('/products', products);
router.use('/cart', cart);
router.use('/orders', orders);
router.use('/payments', payments);
router.use('/subscriptions', subscriptions);
router.use('/admin', admin);
