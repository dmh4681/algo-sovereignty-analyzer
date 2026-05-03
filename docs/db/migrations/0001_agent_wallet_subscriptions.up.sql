-- Migration UP: Agent Wallet + Subscription Billing schema
-- Target: PostgreSQL 14+

begin;

create extension if not exists pgcrypto;

create table if not exists tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create table if not exists agents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  name text not null,
  status text not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_agents_tenant_id on agents(tenant_id);

create table if not exists wallets (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  network text not null,
  address text not null unique,
  custody_type text not null default 'managed',
  status text not null default 'active',
  created_at timestamptz not null default now()
);
create index if not exists idx_wallets_tenant_agent on wallets(tenant_id, agent_id);

create table if not exists payment_requests (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  wallet_id uuid not null references wallets(id),
  asset_id bigint not null,
  amount numeric(38,0) not null,
  to_address text not null,
  status text not null,
  tx_id text,
  round_submitted bigint,
  confirmed_round bigint,
  failure_code text,
  metadata jsonb not null default '{}'::jsonb,
  idempotency_key text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, idempotency_key)
);
create index if not exists idx_payment_requests_tenant_status on payment_requests(tenant_id, status);
create index if not exists idx_payment_requests_tx_id on payment_requests(tx_id);

create table if not exists policy_decisions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  payment_request_id uuid not null references payment_requests(id),
  decision text not null,
  reason_code text,
  details jsonb not null default '{}'::jsonb,
  decided_at timestamptz not null default now()
);
create index if not exists idx_policy_decisions_payment on policy_decisions(payment_request_id);

create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  external_ref text not null,
  email text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  unique (tenant_id, external_ref)
);

create table if not exists plans (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  name text not null,
  amount numeric(38,0) not null,
  asset_id bigint not null,
  interval text not null,
  trial_days integer not null default 0,
  status text not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_plans_tenant_status on plans(tenant_id, status);

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  customer_id uuid not null references customers(id),
  plan_id uuid not null references plans(id),
  status text not null,
  start_at timestamptz not null,
  current_period_start timestamptz,
  current_period_end timestamptz,
  next_billing_at timestamptz,
  cancel_at timestamptz,
  canceled_at timestamptz,
  retry_count integer not null default 0,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_subscriptions_due on subscriptions(tenant_id, status, next_billing_at);

create table if not exists invoices (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  customer_id uuid not null references customers(id),
  subscription_id uuid references subscriptions(id),
  amount_due numeric(38,0) not null,
  amount_paid numeric(38,0) not null default 0,
  asset_id bigint not null,
  status text not null,
  due_at timestamptz,
  paid_at timestamptz,
  payment_request_id uuid references payment_requests(id),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_invoices_tenant_status_due on invoices(tenant_id, status, due_at);

create table if not exists entitlements (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  customer_id uuid not null references customers(id),
  subscription_id uuid references subscriptions(id),
  product_code text not null,
  status text not null,
  starts_at timestamptz,
  ends_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_entitlements_customer_product on entitlements(tenant_id, customer_id, product_code);

create table if not exists webhook_endpoints (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  url text not null,
  secret_hash text not null,
  status text not null default 'active',
  event_filter jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists webhook_deliveries (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  endpoint_id uuid not null references webhook_endpoints(id),
  event_type text not null,
  payload jsonb not null,
  attempt_count integer not null default 0,
  last_http_status integer,
  next_attempt_at timestamptz,
  delivered_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists idx_webhook_deliveries_retry on webhook_deliveries(tenant_id, delivered_at, next_attempt_at);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  actor_type text not null,
  actor_id text,
  action text not null,
  resource_type text not null,
  resource_id text not null,
  trace_id text,
  before_state jsonb,
  after_state jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_audit_logs_tenant_created on audit_logs(tenant_id, created_at desc);

commit;
