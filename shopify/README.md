# Multi-Vendor E-commerce SaaS Platform (Shopify-like)

A production-ready, scalable, multi-tenant e-commerce SaaS. Store owners can create their own stores (store subdomains), manage products, receive orders, and get paid while the platform earns subscription and commission.

Tech stack
- Backend: Node.js, Express, PostgreSQL, Prisma ORM, REST API, JWT auth
- Frontend: Next.js (React), TailwindCSS, Redux Toolkit
- Admin: Next.js (React) admin dashboard
- Payments: Stripe & Razorpay (via webhooks)
- Storage: AWS S3 (or Cloudinary)
- Infra: Docker, Nginx, Vercel (frontend/admin), AWS ECS/RDS or Railway/Fly.io (backend), Terraform-ready

Monorepo structure
- backend/ — API, auth, DB, webhooks
- frontend/ — storefront + tenant routing (subdomains)
- admin-dashboard/ — platform admin UI
- database/ — prisma schema and migrations
- infra/ — Docker, nginx, compose, deploy examples

Quick start (development)
1) Prereqs: Node 18+, pnpm or npm, Docker, PostgreSQL (or use docker compose provided)
2) Copy env templates and fill values
- cp backend/.env.example backend/.env
- cp frontend/.env.example frontend/.env.local
- cp admin-dashboard/.env.example admin-dashboard/.env.local
3) Start DB (docker-compose)
- docker compose -f infra/docker-compose.dev.yml up -d
4) Install deps, generate Prisma, run migrations, seed
- pnpm -r install
- pnpm -C backend prisma:generate
- pnpm -C backend prisma:migrate
- pnpm -C backend seed
5) Run services
- pnpm -C backend dev
- pnpm -C frontend dev
- pnpm -C admin-dashboard dev

Production
- Use infra/Dockerfile.* and infra/nginx for containerized deployment
- Frontend/Admin: Vercel
- Backend: AWS ECS/Fargate or Fly.io. DB: AWS RDS or Neon
- Object storage: S3-compatible (S3, MinIO)

Environment variables
Backend (.env)
- DATABASE_URL=postgresql://user:pass@host:5432/db
- JWT_SECRET=change_me
- PORT=4000
- S3_BUCKET=your-bucket
- S3_REGION=your-region
- S3_ACCESS_KEY_ID=...
- S3_SECRET_ACCESS_KEY=...
- STRIPE_SECRET_KEY=sk_live_or_test
- STRIPE_WEBHOOK_SECRET=whsec_...
- RAZORPAY_KEY_ID=...
- RAZORPAY_KEY_SECRET=...
- PLATFORM_BASE_URL=https://api.yourplatform.com
- FRONTEND_BASE_URL=https://yourplatform.com
- ADMIN_BASE_URL=https://admin.yourplatform.com
- PLATFORM_COMMISSION_BPS=500  # 5%
- SUBSCRIPTION_PROVIDER=stripe  # or razorpay
- EMAIL_FROM=noreply@yourplatform.com
- SMTP_HOST=...
- SMTP_PORT=587
- SMTP_USER=...
- SMTP_PASS=...

Frontend (.env.local)
- NEXT_PUBLIC_API_URL=http://localhost:4000
- NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
- NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_...
- NEXT_PUBLIC_PLATFORM_DOMAIN=localhost

Admin (.env.local)
- NEXT_PUBLIC_API_URL=http://localhost:4000

Key features implemented
- Multi-tenant stores with unique subdomains (store.yourplatform.com)
- Auth: signup/login, email verification, password reset, JWT
- Store management: products, inventory, images (S3)
- Product catalog: categories, slugs, SEO fields
- Cart & checkout: persisted carts, shipping addresses
- Payments: Stripe & Razorpay, commission split (connect-like model via transfer/capture simulation) and ledger
- Orders: status updates, events, tracking fields
- Subscriptions: plans (Basic/Pro/Enterprise), billing cycles, grace period, webhooks
- Themes: simple theme registry (fashion/electronics/minimal) with dynamic rendering
- Analytics: revenue, orders, conversion, top products (charts)
- Security: rate limiting, input validation (Zod), SQL injection protection via Prisma prepared statements, CORS, helmet
- Deployment: Dockerfiles, Nginx for wildcard subdomains, Vercel-ready Next.js

Scripts (root via pnpm workspaces)
- backend:dev — nodemon
- frontend:dev — next dev
- admin:dev — next dev
- prisma:generate, prisma:migrate, seed

Docs
- See backend/README.md and frontend/README.md for API and UI details.

License
- MIT
