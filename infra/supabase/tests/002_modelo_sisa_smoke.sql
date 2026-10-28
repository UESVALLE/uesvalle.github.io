-- Prueba con datos EXCLUSIVAMENTE SINTÉTICOS en PostgreSQL temporal.
-- Se ejecuta tras 001_base_privada_smoke.sql (crea roles dummy/auth en runner).
\set ON_ERROR_STOP on
\i infra/supabase/proposals/002_modelo_sisa_borrador.sql

do $$
declare
 n integer;
 p uuid;
 s uuid;
 l uuid;
 pr uuid;
 ev1 uuid;
 ev2 uuid;
 rejected boolean;
begin
 select count(*) into n from pg_class c
 join pg_namespace ns on ns.oid=c.relnamespace
 where ns.nspname in ('ues_core','ues_ingesta','ues_operacion','ues_calidad')
   and c.relkind in ('r','p');
 if n <> 13 then raise exception 'Esquema de prueba inesperado: % tablas', n; end if;
 if exists (
  select 1 from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
  where ns.nspname in ('ues_core','ues_ingesta','ues_operacion','ues_calidad')
    and c.relkind in ('r','p')
    and (not c.relrowsecurity
      or has_table_privilege('anon',c.oid,'SELECT')
      or has_table_privilege('authenticated',c.oid,'SELECT'))
 ) then raise exception 'RLS/GRANT inválido'; end if;
 if has_schema_privilege('anon','ues_core','USAGE') then
  raise exception 'anon puede ingresar a esquema privado';
 end if;

 insert into ues_core.municipio(divipola,nombre) values('76001','MUNICIPIO SINTETICO');
 insert into ues_core.aro(aro_codigo,nombre) values('ARO-TEST','ARO SINTETICA');
 insert into ues_core.prestador(nombre_normalizado) values('PRESTADOR SINTETICO') returning prestador_id into p;
 insert into ues_core.sistema_abastecimiento(nombre_normalizado,prestador_id,divipola)
 values('SISTEMA SINTETICO',p,'76001') returning sistema_id into s;
 insert into ues_core.sistema_codigo(sistema_id,tipo_codigo,codigo_original,fuente)
 values(s,'CODIGO_ANTERIOR','TEST-SIS-01','SISA');
 insert into ues_core.sistema_codigo(sistema_id,tipo_codigo,codigo_original,fuente,validado,validado_por,validado_en)
 values(s,'CODIGO_ANTERIOR','TEST-SIS-01','SISA',true,'test-runner',now());

 rejected:=false;
 begin
   insert into ues_core.sistema_codigo(sistema_id,tipo_codigo,codigo_original,fuente,validado,validado_por,validado_en)
   values(s,'CODIGO_ANTERIOR','TEST-SIS-01','SISA',true,'test-runner',now());
 exception when unique_violation then rejected:=true; end;
 if not rejected then raise exception 'Alias validado duplicado no rechazado'; end if;

 insert into ues_ingesta.lote(sistema_origen,sha256_archivo,version_etl,registros_leidos)
 values('SISA',repeat('a',64),'TEST-1',2) returning lote_id into l;
 rejected:=false;
 begin
  insert into ues_ingesta.lote(sistema_origen,sha256_archivo,version_etl)
  values('SISA',repeat('a',64),'TEST-1');
 exception when unique_violation then rejected:=true; end;
 if not rejected then raise exception 'Carga duplicada no rechazada'; end if;

 insert into ues_operacion.programacion_mpr(lote_id,ordinal_registro,codigo_sistema_origen,
 sistema_id,divipola,aro_codigo,periodo_anio)
 values(l,1,'TEST-SIS-01',s,'76001','ARO-TEST',2026) returning programacion_id into pr;
 insert into ues_operacion.actividad_sisa(lote_id,ordinal_registro,codigo_actividad,fecha_actividad,
 codigo_sistema_origen,sistema_id,divipola,aro_codigo,estado_homologacion)
 values(l,1,'1.3','2026-10-28','TEST-SIS-01',s,'76001','ARO-TEST','VALIDADO')
 returning actividad_id into ev1;
 insert into ues_operacion.actividad_sisa(lote_id,ordinal_registro,codigo_actividad,fecha_actividad,
 codigo_sistema_origen,sistema_id,divipola,aro_codigo,estado_homologacion)
 values(l,2,'1.4','2026-10-28','TEST-SIS-01',s,'76001','ARO-TEST','VALIDADO')
 returning actividad_id into ev2;
 select count(*) into n from ues_operacion.actividad_sisa
 where sistema_id=s and fecha_actividad='2026-10-28';
 if n <> 2 then raise exception 'Eventos del mismo día incorrectamente agregados'; end if;

 rejected:=false;
 begin
  insert into ues_operacion.cruce_mpr(programacion_id,actividad_id,metodo,estado)
  values(pr,ev1,'CANDIDATO_TEXTO','CONFIRMADO');
 exception when check_violation then rejected:=true; end;
 if not rejected then raise exception 'Coincidencia textual se confirmó sin revisión'; end if;

 insert into ues_operacion.cruce_mpr(programacion_id,actividad_id,metodo,estado,validado_por,validado_en)
 values(pr,ev1,'CODIGO_VALIDADO','CONFIRMADO','revisor-sintetico',now());
 insert into ues_operacion.cruce_mpr(programacion_id,actividad_id,metodo,estado)
 values(pr,ev2,'CANDIDATO_TEXTO','PENDIENTE');
 insert into ues_calidad.muestra(codigo_muestra_origen,fuente_codigo,fuente_dato,sistema_id,fecha_toma)
 values('M-TEST','LAB','SIVICAP',s,'2026-10-28');

 raise notice 'PASS: 13 tablas privadas, RLS/GRANT, deduplicación de lotes, alias validados, 2 eventos y cruces controlados';
end $$;

select 'PASS UESVALLE MODELO V1 SINTETICO' as resultado;
