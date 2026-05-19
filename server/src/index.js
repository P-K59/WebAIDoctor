import express from "express";
import cors from "cors";
import multer from "multer";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { CLIENT_ORIGIN, PORT, specialties } from "./config.js";
import { createHealthAdvice, analyzeReport } from "./healthService.js";
import { detectCityFromIp, geocodeCity, getHospitals } from "./locationService.js";
import { getDoctors } from "./doctorService.js";
import { extractReportText } from "./fileService.js";

const app = express();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distPath = path.resolve(__dirname, "../../client/dist");

app.use(cors({ origin: CLIENT_ORIGIN }));
app.use(express.json({ limit: "1mb" }));
app.use(express.static(distPath));

app.get("/api/meta", (_req, res) => {
  res.json({ specialties });
});

app.get("/api/location", async (_req, res) => {
  try {
    res.json(await detectCityFromIp());
  } catch {
    res.json({ city: "", lat: null, lon: null });
  }
});

app.post("/api/advice", async (req, res, next) => {
  try {
    const result = await createHealthAdvice(req.body.symptoms || "", req.body.city || "");
    if (result.error) return res.status(400).json(result);

    const doctors = req.body.city ? await getDoctors(req.body.city, result.specialty) : [];
    res.json({ ...result, doctors });
  } catch (error) {
    next(error);
  }
});

app.get("/api/doctors", async (req, res, next) => {
  try {
    const city = String(req.query.city || "").trim();
    const specialty = String(req.query.specialty || "General Physician").trim();
    if (!city) return res.status(400).json({ error: "City is required." });
    res.json({ doctors: await getDoctors(city, specialty) });
  } catch (error) {
    next(error);
  }
});

app.get("/api/hospitals", async (req, res, next) => {
  try {
    const city = String(req.query.city || "").trim();
    if (!city) return res.status(400).json({ error: "City is required." });
    const coords = await geocodeCity(city);
    if (!coords.lat || !coords.lon) return res.status(404).json({ error: `Could not find ${city}.` });
    res.json({ ...coords, hospitals: await getHospitals(coords.lat, coords.lon) });
  } catch (error) {
    next(error);
  }
});

app.post("/api/reports/analyze", upload.single("report"), async (req, res, next) => {
  try {
    const mode = req.body.mode || "lab";
    const extracted = req.body.reportText?.trim()
      ? { text: req.body.reportText.trim(), preview: req.body.reportText.trim().slice(0, 3000), error: "" }
      : await extractReportText(req.file, mode);

    if (extracted.error) return res.status(400).json(extracted);

    const analysis = await analyzeReport({
      reportText: extracted.text,
      reportType: req.body.reportType,
      patientContext: req.body.patientContext,
      mode
    });

    res.json({ analysis, preview: extracted.preview });
  } catch (error) {
    next(error);
  }
});

app.get(/.*/, (_req, res) => {
  res.sendFile(path.join(distPath, "index.html"));
});

app.use((error, _req, res, _next) => {
  const message = error?.message || "Unexpected server error.";
  res.status(500).json({ error: message });
});

app.listen(PORT, "127.0.0.1", () => {
  console.log(`AI Doctor API listening on http://127.0.0.1:${PORT}`);
});
