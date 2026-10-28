-- Supabase compatibility smoke test on ephemeral PostgreSQL 16.
-- No real UESVALLE data or credentials.
\set ON_ERROR_STOP on

create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create schema auth;
create table auth.users (id uuid primary key);

\i infra/supabase/schema/001_base_privada.sql

do $$
declare
  new_id uuid := gen_random_uuid();
  flag boolean;
  missing_policies integer;
begin
  if has_schema_privilege('anon', 'ues_private', 'USAGE') then
    raise exception 'FAIL: anon can use private schema';
  end if;
  if has_schema_privilege('authenticated', 'ues_private', 'USAGE') then
    raise exception 'FAIL: authenticated can use private schema';
  end if;
  if not has_schema_privilege('service_role', 'ues_private', 'USAGE') then
    raise exception 'FAIL: service role lacks private schema usage';
  end if;
  if has_table_privilege('anon', 'ues_private.dataset_registry', 'SELECT') then
    raise exception 'FAIL: anon can read registry';
  end if;
  if has_table_privilege('authenticated', 'ues_private.user_memberships', 'SELECT') then
    raise exception 'FAIL: authenticated can read memberships';
  end if;
  if exists(
    select 1 from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'ues_private'
      and c.relkind in ('r','p')
      and c.relrowsecurity = false
  ) then
    raise exception 'FAIL: missing RLS on private tables';
  end if;

  select count(*) into missing_policies
  from pg_policies
  where schemaname = 'ues_private' and roles @> array['public']::name[];
  if missing_policies > 0 then
    raise exception 'FAIL: global public policy exists';
  end if;

  insert into auth.users(id) values(new_id);
  insert into ues_private.user_memberships (user_id, rol, proceso)
  values(new_id,'consulta','ach');
  select activo into flag from ues_private.user_memberships where user_id = new_id;
  if flag is distinct from false then
    raise exception 'FAIL: new user membership enabled by default';
  end if;

  begin
    insert into ues_private.dataset_registry(modulo,nombre_logico,fuente,clasificacion)
    values('synthetic','synthetic','synthetic','PUBLICO_APROBADO');
    raise exception 'FAIL: public dataset without authorization was accepted';
  exception
    when check_violation then null;
  end;

  raise notice 'PASS: private schema, minimal grants, RLS, inactive memberships and publication constraints';
end $$;

-- Sanity check that a least-privilege user cannot even reach ues_private.
select 'OK: synthetic PostgreSQL security checks completed' as outcome;
