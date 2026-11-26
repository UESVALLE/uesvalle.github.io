import { claveCorrecta, crearToken, cookieSesion, cookieBorrar } from './_sesion.js';

const json = (cuerpo, status = 200, extra = {}) =>
  new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...extra },
  });

export default async function handler(request) {
  if (request.method === 'DELETE') {
    return json({ ok: true }, 200, { 'Set-Cookie': cookieBorrar() });
  }
  if (request.method !== 'POST') return json({ error: 'Método no permitido' }, 405);

  if (!process.env.PAER_PASSWORD || !process.env.PAER_SESSION_SECRET) {
    return json({ error: 'Acceso no configurado en el servidor.' }, 500);
  }

  let clave = '';
  try {
    ({ clave } = await request.json());
  } catch {
    return json({ error: 'Solicitud inválida' }, 400);
  }

  if (!claveCorrecta(clave)) {
    await new Promise((r) => setTimeout(r, 700)); // frena intentos repetidos
    return json({ error: 'Contraseña incorrecta.' }, 401);
  }
  return json({ ok: true }, 200, { 'Set-Cookie': cookieSesion(crearToken()) });
}
