export default function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({
    ok: true,
    service: "UESVALLE AI API",
    provider: "NVIDIA",
    model: process.env.NVIDIA_MODEL || "nvidia/nemotron-3-super-120b-a12b",
    hasApiKey: Boolean(process.env.NVIDIA_API_KEY)
  });
}
