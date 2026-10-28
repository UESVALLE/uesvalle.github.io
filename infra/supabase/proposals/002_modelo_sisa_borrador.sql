-- Propuesta NO APLICADA al proyecto Supabase real: modelo relacional SISA V1.
-- Privado por defecto. Sin datos reales, sin usuarios, sin roles públicos.
-- Debe revisarse contra el DDL exacto del respaldo antiguo y requerimientos UESVALLE.
begin;

create schema if not exists ues_core;
create schema if not exists ues_ingesta;
create schema if not exists ues_operacion;
create schema if not exists ues_calidad;

revoke all on schema ues_core, ues_ingesta, ues_operacion, ues_calidad from public, anon, authenticated;

create table if not exists ues_core.municipio (
  divipola char(5) primary key,
  nombre text not null,
  activo boolean not null default true
);

create table if not exists ues_core.aro (
  aro_codigo text primary key,
  nombre text not null
);

create table if not exists ues_core.municipio_aro (
  divipola char(5) not null references ues_core.municipio(divipola),
  aro_codigo text not null references ues_core.aro(aro_codigo),
  vigente_desde date not null,
  vigente_hasta date,
  primary key (divipola, aro_codigo, vigente_desde),
  constraint municipio_aro_fechas check (vigente_hasta is null or vigente_hasta >= vigente_desde)
);

create table if not exists ues_core.prestador (
  prestador_id uuid primary key default gen_random_uuid(),
  nombre_normalizado text not null,
  identificador_sspd text,
  fecha_registro timestamptz not null default now()
);

create table if not exists ues_core.sistema_abastecimiento (
  sistema_id uuid primary key default gen_random_uuid(),
  codigo_maestro text unique,
  nombre_normalizado text not null,
  divipola char(5) references ues_core.municipio(divipola),
  prestador_id uuid references ues_core.prestador(prestador_id),
  estado_validacion text not null default 'PENDIENTE'
    check (estado_validacion in ('PENDIENTE','VALIDADO','CONFLICTO')),
  created_at timestamptz not null default now()
);

create table if not exists ues_core.sistema_codigo (
  alias_id bigint generated always as identity primary key,
  sistema_id uuid not null references ues_core.sistema_abastecimiento(sistema_id),
  tipo_codigo text not null,
  codigo_original text not null,
  fuente text not null,
  validado boolean not null default false,
  validado_por text,
  validado_en timestamptz,
  created_at timestamptz not null default now(),
  constraint alias_aprobacion check (
    not validado or (validado_por is not null and validado_en is not null)
  )
);
-- Impide usar un mismo alias de sistema confirmado para sistemas diferentes.
-- Los alias sin validar pueden coexistir para resolver colisiones.
create unique index if not exists uniq_codigo_validado
  on ues_core.sistema_codigo (fuente, tipo_codigo, codigo_original)
  where validado;

create table if not exists ues_ingesta.lote (
  lote_id uuid primary key default gen_random_uuid(),
  sistema_origen text not null,
  sha256_archivo char(64) not null,
  fecha_corte date,
  fecha_importacion timestamptz not null default now(),
  version_etl text not null,
  estado text not null default 'RECIBIDO'
    check (estado in ('RECIBIDO','VALIDANDO','RECHAZADO','APROBADO','PUBLICADO')),
  registros_leidos bigint not null default 0 check (registros_leidos >= 0),
  registros_aceptados bigint not null default 0 check (registros_aceptados >= 0),
  registros_rechazados bigint not null default 0 check (registros_rechazados >= 0),
  -- El archivo y su huella no deben contener datos personales en metadatos de ruta.
  constraint lote_conteos check (registros_aceptados + registros_rechazados <= registros_leidos),
  unique (sistema_origen, sha256_archivo, version_etl)
);

create table if not exists ues_ingesta.incidencia (
  incidencia_id bigint generated always as identity primary key,
  lote_id uuid not null references ues_ingesta.lote(lote_id),
  ordinal_registro integer,
  codigo_incidente text not null,
  severidad text not null check (severidad in ('INFO','ADVERTENCIA','ERROR','CRITICO')),
  resuelto boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists ues_operacion.programacion_mpr (
  programacion_id uuid primary key default gen_random_uuid(),
  lote_id uuid not null references ues_ingesta.lote(lote_id),
  ordinal_registro integer not null check (ordinal_registro > 0),
  codigo_sistema_origen text,
  sistema_id uuid references ues_core.sistema_abastecimiento(sistema_id),
  divipola char(5) references ues_core.municipio(divipola),
  aro_codigo text references ues_core.aro(aro_codigo),
  periodo_anio integer not null check (periodo_anio between 2000 and 2100),
  funcionario_origen text,
  prestador_origen text,
  unique (lote_id, ordinal_registro)
);

create table if not exists ues_operacion.actividad_sisa (
  actividad_id uuid primary key default gen_random_uuid(),
  lote_id uuid not null references ues_ingesta.lote(lote_id),
  ordinal_registro integer not null check (ordinal_registro > 0),
  id_sisa text, -- Si SISA ofrece ID estable; no inventarlo.
  codigo_actividad text not null,
  fecha_actividad date not null,
  codigo_sistema_origen text,
  sistema_id uuid references ues_core.sistema_abastecimiento(sistema_id),
  divipola char(5) references ues_core.municipio(divipola),
  aro_codigo text references ues_core.aro(aro_codigo),
  acta text,
  consecutivo_visita text,
  funcionario_origen text,
  estado text,
  estado_homologacion text not null default 'PENDIENTE'
    check (estado_homologacion in ('PENDIENTE','VALIDADO','AMBIGUO','NO_ENCONTRADO')),
  registrado_en timestamptz not null default now(),
  unique (lote_id, ordinal_registro),
  constraint actividad_sistema_validado check (estado_homologacion <> 'VALIDADO' or sistema_id is not null)
);
create index if not exists idx_actividad_sisa_fecha on ues_operacion.actividad_sisa(fecha_actividad);
create index if not exists idx_actividad_sisa_sistema on ues_operacion.actividad_sisa(sistema_id, codigo_actividad);

create table if not exists ues_operacion.cruce_mpr (
  cruce_id uuid primary key default gen_random_uuid(),
  programacion_id uuid references ues_operacion.programacion_mpr(programacion_id),
  actividad_id uuid not null references ues_operacion.actividad_sisa(actividad_id),
  metodo text not null check (metodo in ('CODIGO_VALIDADO','CANDIDATO_TEXTO','MANUAL','SIN_CRUCE')),
  estado text not null default 'PENDIENTE'
    check (estado in ('PENDIENTE','CONFIRMADO','RECHAZADO')),
  puntaje numeric(7,3),
  validado_por text,
  validado_en timestamptz,
  constraint cruce_mpr_confirmacion check (
    estado <> 'CONFIRMADO' or
    (metodo in ('CODIGO_VALIDADO','MANUAL') and programacion_id is not null
     and validado_por is not null and validado_en is not null)
  )
);
create unique index if not exists uniq_cruce_programacion_actividad
 on ues_operacion.cruce_mpr (programacion_id, actividad_id)
 where programacion_id is not null;

create table if not exists ues_calidad.muestra (
  muestra_id uuid primary key default gen_random_uuid(),
  lote_id uuid references ues_ingesta.lote(lote_id),
  codigo_muestra_origen text not null,
  fuente_codigo text not null,
  sistema_id uuid references ues_core.sistema_abastecimiento(sistema_id),
  fecha_toma date,
  fecha_resultado date,
  laboratorio_origen text,
  fuente_dato text not null,
  validacion text not null default 'PENDIENTE',
  unique(fuente_dato, fuente_codigo, codigo_muestra_origen)
);

create table if not exists ues_calidad.resultado_parametro (
  resultado_id uuid primary key default gen_random_uuid(),
  muestra_id uuid not null references ues_calidad.muestra(muestra_id),
  parametro_origen text not null,
  valor_numerico numeric,
  valor_texto text,
  unidad text,
  metodo text,
  estado_validacion text not null default 'PENDIENTE',
  constraint resultado_no_vacio check (valor_numerico is not null or valor_texto is not null)
);

-- Defensa en profundidad, no autorización completa: no hay políticas de usuario.
alter table ues_core.municipio enable row level security;
alter table ues_core.aro enable row level security;
alter table ues_core.municipio_aro enable row level security;
alter table ues_core.prestador enable row level security;
alter table ues_core.sistema_abastecimiento enable row level security;
alter table ues_core.sistema_codigo enable row level security;
alter table ues_ingesta.lote enable row level security;
alter table ues_ingesta.incidencia enable row level security;
alter table ues_operacion.programacion_mpr enable row level security;
alter table ues_operacion.actividad_sisa enable row level security;
alter table ues_operacion.cruce_mpr enable row level security;
alter table ues_calidad.muestra enable row level security;
alter table ues_calidad.resultado_parametro enable row level security;

revoke all on all tables in schema ues_core, ues_ingesta, ues_operacion, ues_calidad from public, anon, authenticated;
revoke all on all sequences in schema ues_core, ues_ingesta, ues_operacion, ues_calidad from public, anon, authenticated;
grant usage on schema ues_core, ues_ingesta, ues_operacion, ues_calidad to service_role;
grant select, insert, update, delete on all tables in schema ues_core, ues_ingesta, ues_operacion, ues_calidad to service_role;
grant usage, select on all sequences in schema ues_core, ues_ingesta, ues_operacion, ues_calidad to service_role;
alter default privileges in schema ues_core, ues_ingesta, ues_operacion, ues_calidad
  revoke all on tables from public, anon, authenticated;
alter default privileges in schema ues_core, ues_ingesta, ues_operacion, ues_calidad
  revoke all on sequences from public, anon, authenticated;
commit;
