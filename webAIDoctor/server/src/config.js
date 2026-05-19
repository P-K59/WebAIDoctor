import "dotenv/config";
import Groq from "groq-sdk";

export const PORT = Number(process.env.PORT || 5050);
export const CLIENT_ORIGIN = process.env.CLIENT_ORIGIN || "http://127.0.0.1:5173";
export const GROQ_MODEL = process.env.GROQ_MODEL || "llama-3.3-70b-versatile";
export const MODEL = GROQ_MODEL;
export const OLLAMA_MODEL = process.env.OLLAMA_MODEL || "medgemma:4b";
export const OLLAMA_CHAT_URL = process.env.OLLAMA_CHAT_URL || "http://127.0.0.1:11434/api/chat";

export const specialties = [
  "General Physician",
  "Dentist",
  "Cardiologist",
  "Pediatrician",
  "Dermatologist",
  "Gynecologist",
  "Orthopedist"
];

export const groq = process.env.GROQ_API_KEY
  ? new Groq({ apiKey: process.env.GROQ_API_KEY })
  : null;

export const browserHeaders = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.9",
  Referer: "https://www.google.com/"
};
