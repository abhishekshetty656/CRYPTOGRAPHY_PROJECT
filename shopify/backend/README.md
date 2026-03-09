Backend API

Stack
- Node.js, Express, Prisma, PostgreSQL

Run locally
- Copy .env.example to .env and fill
- Start Postgres via docker compose from infra/
- npm install
- npx prisma generate
- npx prisma migrate dev --name init
- npm run dev

API Outline
- POST /api/auth/signup — email, password
- POST /api/auth/login — email, password
- POST /api/stores — create store (auth)
- GET /api/stores/mine — list my stores (auth)
- GET /api/stores/:subdomain — get store by subdomain
- POST /api/products — create (auth)
- PUT /api/products/:id — update (auth)
- DELETE /api/products/:id — delete (auth)
- GET /api/products/by-store/:storeId — list products for store
- POST /api/cart/add — add to cart
- POST /api/cart/update — update qty/remove
- POST /api/orders/checkout — create order from cart
- POST /api/payments/create-intent — Stripe or Razorpay intent
- POST /api/payments/stripe/webhook — Stripe webhook
- GET /api/subscriptions/plans — list plans
- POST /api/subscriptions/assign — attach plan to store
- GET /api/admin/stats — requires ADMIN JWT

Security
- JWT in Authorization: Bearer <token>
- Rate limit, helmet, Zod validation
