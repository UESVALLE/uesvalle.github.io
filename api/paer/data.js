import { get } from '@vercel/blob';
import { leerCookie, tokenValido } from './_sesion.js';

// Ruta del archivo dentro del almacén Blob PRIVADO (lo sube actualizar_paer.py).
const RUTA = 'paer/paer_tablero.json';

export default async function handler(request) {
  if (!tokenValido(leerCookie(request))) {
    return new Response(JSON.stringify({ error: 'No autorizado' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });
  }

  const r = await get(RUTA, { access: 'private', useCache: false });
  if (!r || r.statusCode !== 200) {
    return new Response(JSON.stringify({ error: 'Datos no disponibles' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });
  }
  return new Response(r.stream, {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': 'private, no-store',
    },
  });
}
