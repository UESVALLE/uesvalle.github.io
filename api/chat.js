import { retrieve } from "../lib/retriever.js";
import { askNemotron } from "../lib/nvidia.js";

const MAX_QUESTION = 2500;

function normalizeOrigin(value) {
  if (!value) return null;

  const normalized = String(value).trim().replace(/\/+$/, "");

  return normalized.startsWith("http://") || normalized.startsWith("https://")
    ? normalized
    : `https://${normalized}`;
}

function allowedOrigin(origin) {
  if (!origin) return true;

  const allowed = new Set(
    [
      process.env.ALLOWED_ORIGIN || "https://uesvalle.github.io",
      process.env.VERCEL_URL,
      process.env.VERCEL_BRANCH_URL,
      process.env.VERCEL_PROJECT_PRODUCTION_URL
    ]
      .filter(Boolean)
      .map(normalizeOrigin)
  );

  return allowed.has(normalizeOrigin(origin));
}

function setCors(req, res) {
  const origin = req.headers.origin;

  if (origin && allowedOrigin(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }

  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

export default async function handler(req, res) {
  setCors(req, res);
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") return res.status(204).end();

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Método no permitido." });
  }

  if (!allowedOrigin(req.headers.origin)) {
    return res.status(403).json({ error: "Origen no autorizado." });
  }

  const question = String(req.body?.message || "").trim();

  if (!question) {
    return res.status(400).json({ error: "Escriba una pregunta." });
  }

  if (question.length > MAX_QUESTION) {
    return res.status(400).json({ error: "La pregunta es demasiado larga." });
  }

  try {
    const chunks = await retrieve(question, 5);

    const context = chunks
      .map(
        (chunk, index) =>
          `[FUENTE ${index + 1}: ${chunk.path}]\n${chunk.text}`
      )
      .join("\n\n");

    const result = await askNemotron({ question, context });

    const seen = new Set();

    const sources = chunks
      .filter((chunk) => {
        if (seen.has(chunk.path)) return false;
        seen.add(chunk.path);
        return true;
      })
      .map(({ title, path, sourceUrl }) => ({
        title,
        path,
        url: sourceUrl
      }));

    return res.status(200).json({
      answer: result.answer,
      sources,
      model: result.model
    });
  } catch (error) {
    console.error("UESVALLE AI error:", error?.message || error);

    return res.status(500).json({
      error: "No fue posible completar la consulta."
    });
  }
}
