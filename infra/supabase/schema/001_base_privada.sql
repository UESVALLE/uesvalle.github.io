-- UESVALLE / Borrador técnico de migración 001.
-- NO EJECUTADO. Aplicar sólo en un proyecto institucional aprobado, inicialmente de PRUEBAS.
-- No contiene datos reales, credenciales ni permisos públicos de lectura.
begin;

create schema if not exists ues_private;
revoke all on schema ues_private from public, anon, authenticated;

create table if not exists ues_private.user_memberships (
  membership_id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  rol text not null check (rol in (
    'administrador_tecnico', 'responsable_dato', 'coordinador', 'profesional_aro', 'consulta'
  )),
  proceso text not null,
  aro text,
  municipio_divipola char(5),
  activo boolean not null default false,
  valido_desde timestamptz not null default now(),
  valido_hasta timestamptz,
  creado timestamptz not null default now(),
  constraint membresia_vigencia check (valido_hasta is null or valido_hasta > valido_desde)
);
create index if not exists idx_membership_user on ues_private.user_memberships(user_id, activo);
create index if not exists idx_membership_scope on ues_private.user_memberships(proceso, aro, municipio_divipola);
alter table ues_private.user_memberships enable row level security;
-- No policies de lectura pública/autenticada: denegación inicial.

create table if not exists ues_private.dataset_registry (
  dataset_id bigint generated always as identity primary key,
  modulo text not null,
  nombre_logico text not null,
  fuente text not null,
  clasificacion text not null default 'POR_CLASIFICAR'
    check (clasificacion in ('POR_CLASIFICAR','PUBLICO_APROBADO','INTERNO','RESTRINGIDO')),
  propietario_dato text,
  ultima_ingesta timestamptz,
  calidad_estado text not null default 'PENDIENTE',
  aprobado_publicacion_por text,
  aprobado_publicacion_en timestamptz,
  creado timestamptz not null default now(),
  unique (modulo, nombre_logico),
  constraint aprobar_publico_con_responsable check (
    clasificacion <> 'PUBLICO_APROBADO' or
    (aprobado_publicacion_por is not null and aprobado_publicacion_en is not null)
  )
);
alter table ues_private.dataset_registry enable row level security;

create table if not exists ues_private.audit_events (
  event_id bigint generated always as identity primary key,
  event_at timestamptz not null default now(),
  actor_id uuid,
  modulo text not null,
  operacion text not null,
  resultado text not null check (resultado in ('PERMITIDO','DENEGADO','ERROR')),
  reference_id text,
  request_id uuid,
  -- Prohibido: contraseñas, JWT, cookies, datos personales crudos en el log.
  resumen_seguro text
);
create index if not exists idx_audit_when on ues_private.audit_events(event_at desc);
alter table ues_private.audit_events enable row level security;

-- Grant explícito sólo para servicios servidor autorizados. No conceder a anon/authenticated.
revoke all on all tables in schema ues_private from public, anon, authenticated;
revoke all on all sequences in schema ues_private from public, anon, authenticated;
grant usage on schema ues_private to service_role;
grant select, insert, update, delete on all tables in schema ues_private to service_role;
grant usage, select on all sequences in schema ues_private to service_role;

-- Importante: no crear política pública de Storage.
-- Crear bucket PRIVADO vía API/administración y confirmar storage.buckets.public=false.
-- Más adelante: implementar API que valide JWT + membresía activa + ámbito,
-- y permisos RLS específicos para tablas de datos de cada proceso.
commit;
