// Utilidades de sesión del tablero PAER (validación en servidor).
// Variables de entorno requeridas (se configuran en Vercel, nunca en el código):
//   PAER_PASSWORD        clave de acceso al tablero PAER
//   PAER_SESSION_SECRET  secreto largo y aleatorio para firmar la cookie de sesión
import { createHmac, createHash, timingSafeEqual } from 'node:crypto';

export const COOKIE = 'paer_sesion';
const DURACION_S = 8 * 60 * 60; // 8 horas

const firma = (texto) =>
  createHmac('sha256', process.env.PAER_SESSION_SECRET || '').update(texto).digest('base64url');

export function claveCorrecta(intento) {
  const esperada = process.env.PAER_PASSWORD;
  if (!esperada || typeof intento !== 'string') return false;
  const a = createHash('sha256').update(intento).digest();
  const b = createHash('sha256').update(esperada).digest();
  return timingSafeEqual(a, b);
}

export function crearToken() {
  const exp = Math.floor(Date.now() / 1000) + DURACION_S;
  return `${exp}.${firma(String(exp))}`;
}

export function tokenValido(token) {
  if (!process.env.PAER_SESSION_SECRET || !token) return false;
  const [exp, sig] = String(token).split('.');
  if (!exp || !sig || Number(exp) < Date.now() / 1000) return false;
  const esperada = firma(exp);
  const a = Buffer.from(sig);
  const b = Buffer.from(esperada);
  return a.length === b.length && timingSafeEqual(a, b);
}

export function leerCookie(request, nombre = COOKIE) {
  const raw = request.headers.get('cookie') || '';
  for (const parte of raw.split(';')) {
    const [k, ...v] = parte.trim().split('=');
    if (k === nombre) return v.join('=');
  }
  return '';
}

export const cookieSesion = (token) =>
  `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${DURACION_S}`;
export const cookieBorrar = () =>
  `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`;
