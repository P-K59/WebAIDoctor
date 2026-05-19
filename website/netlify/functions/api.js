import { specialties } from "../../server/src/config.js";
import { createHealthAdvice, analyzeReport } from "../../server/src/healthService.js";
import { detectCityFromIp, geocodeCity, getHospitals } from "../../server/src/locationService.js";
import { getDoctors } from "../../server/src/doctorService.js";
import { extractReportText } from "../../server/src/fileService.js";

const jsonHeaders = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
};

function json(statusCode, body) {
  return {
    statusCode,
    headers: jsonHeaders,
    body: JSON.stringify(body)
  };
}

function getApiPath(event) {
  const rawPath = event.rawUrl ? new URL(event.rawUrl).pathname : event.path;
  return rawPath.replace(/^\/(?:\.netlify\/functions\/api|api)/, "/api") || "/api";
}

function getQuery(event) {
  if (event.rawUrl) return new URL(event.rawUrl).searchParams;
  return new URLSearchParams(event.rawQuery || "");
}

function parseJsonBody(event) {
  if (!event.body) return {};
  const body = event.isBase64Encoded ? Buffer.from(event.body, "base64").toString("utf8") : event.body;
  return JSON.parse(body || "{}");
}

async function parseForm(event) {
  const protocol = event.headers["x-forwarded-proto"] || "https";
  const host = event.headers.host || "localhost";
  const url = `${protocol}://${host}${event.path}`;
  const body = event.isBase64Encoded ? Buffer.from(event.body || "", "base64") : event.body || "";
  const request = new Request(url, {
    method: event.httpMethod,
    headers: event.headers,
    body
  });
  const formData = await request.formData();
  const fields = {};
  let upload = null;

  for (const [key, value] of formData.entries()) {
    if (value && typeof value === "object" && "arrayBuffer" in value) {
      const buffer = Buffer.from(await value.arrayBuffer());
      upload = {
        buffer,
        size: buffer.length,
        originalname: value.name || "upload",
        mimetype: value.type || "application/octet-stream"
      };
    } else {
      fields[key] = String(value || "");
    }
  }

  return { fields, upload };
}

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: jsonHeaders, body: "" };
  }

  try {
    const path = getApiPath(event);
    const query = getQuery(event);

    if (event.httpMethod === "GET" && path === "/api/meta") {
      return json(200, { specialties });
    }

    if (event.httpMethod === "GET" && path === "/api/health") {
      return json(200, {
        ok: true,
        runtime: "netlify-functions",
        hasGroqKey: Boolean(process.env.GROQ_API_KEY)
      });
    }

    if (event.httpMethod === "GET" && path === "/api/location") {
      try {
        return json(200, await detectCityFromIp());
      } catch {
        return json(200, { city: "", lat: null, lon: null });
      }
    }

    if (event.httpMethod === "POST" && path === "/api/advice") {
      const body = parseJsonBody(event);
      const result = await createHealthAdvice(body.symptoms || "", body.city || "");
      if (result.error) return json(400, result);

      const doctors = body.city ? await getDoctors(body.city, result.specialty) : [];
      return json(200, { ...result, doctors });
    }

    if (event.httpMethod === "GET" && path === "/api/doctors") {
      const city = String(query.get("city") || "").trim();
      const specialty = String(query.get("specialty") || "General Physician").trim();
      if (!city) return json(400, { error: "City is required." });
      return json(200, { doctors: await getDoctors(city, specialty) });
    }

    if (event.httpMethod === "GET" && path === "/api/hospitals") {
      const city = String(query.get("city") || "").trim();
      if (!city) return json(400, { error: "City is required." });
      const coords = await geocodeCity(city);
      if (!coords.lat || !coords.lon) return json(404, { error: `Could not find ${city}.` });
      return json(200, { ...coords, hospitals: await getHospitals(coords.lat, coords.lon) });
    }

    if (event.httpMethod === "POST" && path === "/api/reports/analyze") {
      const { fields, upload } = await parseForm(event);
      const mode = fields.mode || "lab";
      const extracted = fields.reportText?.trim()
        ? { text: fields.reportText.trim(), preview: fields.reportText.trim().slice(0, 3000), error: "" }
        : await extractReportText(upload, mode);

      if (extracted.error) return json(400, extracted);

      const analysis = await analyzeReport({
        reportText: extracted.text,
        reportType: fields.reportType,
        patientContext: fields.patientContext,
        mode
      });

      return json(200, { analysis, preview: extracted.preview });
    }

    return json(404, { error: "API route not found." });
  } catch (error) {
    return json(500, { error: error?.message || "Unexpected server error." });
  }
}
