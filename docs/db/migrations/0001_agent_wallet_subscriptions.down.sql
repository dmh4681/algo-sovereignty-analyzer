-- Migration DOWN: Agent Wallet + Subscription Billing schema rollback

begin;

drop table if exists audit_logs;
drop table if exists webhook_deliveries;
drop table if exists webhook_endpoints;
drop table if exists entitlements;
drop table if exists invoices;
drop table if exists subscriptions;
drop table if exists plans;
drop table if exists customers;
drop table if exists policy_decisions;
drop table if exists payment_requests;
drop table if exists wallets;
drop table if exists agents;
drop table if exists tenants;

commit;
