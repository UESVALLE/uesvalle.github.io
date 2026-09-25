import { SOURCES, SOURCE_BASE } from "./ai-sources.js";

let cache = null;
let cacheAt = 0;
const CACHE_MS = 5 * 60 * 1000;

function normalize(value = "") {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s.-]/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokens(value = "") {
  const stop = new Set([
    "de","la","el","los","las","un","una","unos","unas","y","o","en","del","al",
    "que","como","cual","cuales","para","por","con","se","es","son","su","sus",
    "me","mi","quiero","puede","puedes","donde","cuando","este","esta","estos","estas"
  ]);

  return normalize(value)
    .split(" ")
    .filter((t) => t.length > 2 && !stop.has(t));
}

function chunkText(text, source, size = 2200, overlap = 250) {
  const clean = String(text || "").replace(/\r/g, "").trim();
  const chunks = [];
  let start = 0;
  let n = 0;

  while (start < clean.length) {
    let end = Math.min(start + size, clean.length);

    if (end < clean.length) {
      const boundary = Math.max(
        clean.lastIndexOf("\n\n", end),
        clean.lastIndexOf("\n", end),
        clean.lastIndexOf(". ", end)
      );
      if (boundary > start + 700) end = boundary + 1;
    }

    const textChunk = clean.slice(start, end).trim();

    if (textChunk) {
      chunks.push({
        id: `${source.id}-${++n}`,
        title: source.title,
        path: source.path,
        sourceUrl: SOURCE_BASE + source.path,
        text: textChunk
      });
    }

    if (end >= clean.length) break;
    start = Math.max(end - overlap, start + 1);
  }

  return chunks;
}

async function loadCorpus() {
  const now = Date.now();
  if (cache && now - cacheAt < CACHE_MS) return cache;

  const results = await Promise.all(
    SOURCES.map(async (source) => {
      const response = await fetch(source.url, {
        headers: { "User-Agent": "UESVALLE-AI-Pilot/1.0" }
      });

      if (!response.ok) {
        throw new Error(`No se pudo cargar ${source.path}: HTTP ${response.status}`);
      }

      return chunkText(await response.text(), source);
    })
  );

  cache = results.flat();
  cacheAt = now;
  return cache;
}

function scoreChunk(chunk, queryTokens) {
  const haystack = normalize(`${chunk.title} ${chunk.path} ${chunk.text}`);
  let score = 0;

  for (const token of queryTokens) {
    if (haystack.includes(token)) score += 1;
    if (normalize(chunk.title).includes(token)) score += 2;
    if (normalize(chunk.path).includes(token)) score += 2;
  }

  return score;
}

export async function retrieve(question, topK = 5) {
  const corpus = await loadCorpus();
  const qTokens = tokens(question);

  const ranked = corpus
    .map((chunk) => ({ ...chunk, score: scoreChunk(chunk, qTokens) }))
    .sort((a, b) => b.score - a.score);

  const positive = ranked.filter((item) => item.score > 0);
  return (positive.length ? positive : ranked).slice(0, topK);
}
