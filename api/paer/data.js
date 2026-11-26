import { get, list } from '@vercel/blob';
import { leerCookie, tokenValido } from './_sesion.js';

// Toma el archivo "paer_tablero*.json" más reciente del almacén Blob PRIVADO
// (en la raíz o dentro de la carpeta paer/). Subir uno nuevo basta para actualizar.
let cache = { ruta: '', hasta: 0 };

async function rutaReciente() {
  if (cache.ruta && Date.now() < cache.hasta) return cache.ruta;
  const { blobs } = await list({ limit: 200 });
  const c = blobs
    .filter((b) => /(^|\/)paer_tablero[^/]*\.json$/i.test(b.pathname))
    .sort((a, b) => new Date(b.uploadedAt) - new Date(a.uploadedAt));
  cache = { ruta: c[0]?.pathname || '', hasta: Date.now() + 30_000 };
  return cache.ruta;
}

const jsonErr = (error, status) =>
  new Response(JSON.stringify({ error }), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

export async function GET(request) {
  if (!tokenValido(leerCookie(request))) return jsonErr('No autorizado', 401);

  const ruta = await rutaReciente();
  if (!ruta) return jsonErr('Datos no disponibles', 404);

  const r = await get(ruta, { access: 'private', useCache: false });
  if (!r || r.statusCode !== 200) return jsonErr('Datos no disponibles', 404);

  return new Response(r.stream, {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': 'private, no-store',
    },
  });
}
