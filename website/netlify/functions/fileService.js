import pdfParse from "pdf-parse/lib/pdf-parse.js";

export async function extractReportText(file, mode) {
  if (!file) return { text: "", preview: "", error: "Please upload a report file." };
  if (file.size > 10 * 1024 * 1024) return { text: "", preview: "", error: "Maximum upload size is 10 MB." };

  const name = file.originalname.toLowerCase();
  const mimetype = file.mimetype || "";

  if (name.endsWith(".txt") || name.endsWith(".csv") || mimetype.startsWith("text/")) {
    const text = file.buffer.toString("utf8").trim();
    return { text, preview: text.slice(0, 3000), error: text ? "" : "The text file is empty." };
  }

  if (name.endsWith(".pdf") || mimetype === "application/pdf") {
    try {
      const parsed = await pdfParse(file.buffer);
      const text = (parsed.text || "").trim();
      if (text.length < 30) {
        return {
          text: "",
          preview: "",
          error: "This PDF appears scanned or image-based. The Node version currently supports text-based PDFs; paste the report text or upload TXT/CSV."
        };
      }
      return { text, preview: text.slice(0, 3000), error: "" };
    } catch (error) {
      return { text: "", preview: "", error: `PDF reading failed: ${error.message.slice(0, 90)}` };
    }
  }

  if (mimetype.startsWith("image/")) {
    if (mode === "imaging") {
      return {
        text: "[MEDICAL_IMAGE_UPLOADED]",
        preview: `Image uploaded: ${file.originalname}`,
        error: ""
      };
    }
    return {
      text: "",
      preview: "",
      error: "Image OCR is not enabled in the Node version yet. Upload a text-based PDF/TXT/CSV or paste the report text."
    };
  }

  return { text: "", preview: "", error: "Unsupported file type. Upload PDF, TXT, CSV, JPG, or PNG." };
}
