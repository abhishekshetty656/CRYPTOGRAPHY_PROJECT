import { Router } from 'express';
import { prisma } from '../../db.js';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { z } from 'zod';

const router = Router();

router.post('/signup', async (req, res) => {
  const schema = z.object({ email: z.string().email(), password: z.string().min(6), name: z.string().optional() });
  const data = schema.parse(req.body);
  const existing = await prisma.user.findUnique({ where: { email: data.email } });
  if (existing) return res.status(400).json({ error: 'Email already in use' });
  const hash = await bcrypt.hash(data.password, 10);
  const user = await prisma.user.create({ data: { email: data.email, passwordHash: hash, name: data.name, role: 'MERCHANT' } });
  // TODO: send verification email
  const token = jwt.sign({ id: user.id, role: user.role }, process.env.JWT_SECRET as string, { expiresIn: '7d' });
  res.json({ token, user });
});

router.post('/login', async (req, res) => {
  const schema = z.object({ email: z.string().email(), password: z.string() });
  const { email, password } = schema.parse(req.body);
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) return res.status(400).json({ error: 'Invalid credentials' });
  const ok = await bcrypt.compare(password, user.passwordHash);
  if (!ok) return res.status(400).json({ error: 'Invalid credentials' });
  const token = jwt.sign({ id: user.id, role: user.role }, process.env.JWT_SECRET as string, { expiresIn: '7d' });
  res.json({ token, user });
});

export default router;
