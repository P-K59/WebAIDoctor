import { specialties } from "./config.js";
import { createChatCompletion } from "./llmClient.js";

const emergencyKeywords = [
  "chest pain",
  "breathing difficulty",
  "unconscious",
  "severe bleeding",
  "heart attack",
  "stroke",
  "no pulse",
  "seizure",
  "not breathing",
  "can't breathe",
  "collapsed"
];

const systemPrompt = `You are an AI healthcare assistant.

Format your response in simple markdown with short, clear bullet points.
Use these exact markdown headers:
## Quick Summary
## Possible Reasons
## Do
## Don't
## OTC Medicine Options
## When to See a Doctor

Rules:
- Use bullet points under every header.
- Keep each bullet under 30 words.
- Use simple words a patient can understand.
- Avoid long paragraphs.
- Keep the full answer short and easy to scan.
- Mention 2-4 possible reasons only, never as a final diagnosis.
- In OTC Medicine Options, suggest only common over-the-counter active ingredients or medicine types that may fit the symptoms.
- Do not give prescription-only medicines, antibiotics, steroids, injections, controlled drugs, or exact prescription plans.
- Do not give exact dosage schedules.
- Tell the user to follow the package label or ask a pharmacist/doctor when needed.
- In When to See a Doctor, include urgent red flags first.
- End with one short reassurance-focused next step.

Do not diagnose. Do not prescribe prescription medicines. Encourage clinician confirmation.`;

export function checkEmergency(symptoms = "") {
  const lower = symptoms.toLowerCase();
  return emergencyKeywords.some((word) => lower.includes(word));
}

export async function inferSpecialty(symptoms = "") {
  try {
    const text = await createChatCompletion({
      temperature: 0.05,
      max_tokens: 20,
      messages: [
        {
          role: "user",
          content: `Symptoms: ${symptoms.slice(0, 300)}
Best specialty? Reply with just one: ${specialties.join(", ")}`
        }
      ]
    });

    return specialties.find((specialty) => text.toLowerCase().includes(specialty.toLowerCase())) || "General Physician";
  } catch {
    return "General Physician";
  }
}

export async function createHealthAdvice(symptoms = "", city = "") {
  if (!symptoms.trim()) {
    return { error: "Describe your symptoms first." };
  }

  const isEmergency = checkEmergency(symptoms);
  const specialty = await inferSpecialty(symptoms);

  if (isEmergency) {
    return {
      isEmergency,
      specialty,
      advice:
        "This sounds potentially urgent. Please call emergency services such as 108, 112, or 102, or visit the nearest emergency department immediately. Use this app only after urgent safety is handled."
    };
  }

  const advice = await createChatCompletion({
    temperature: 0.25,
    max_tokens: 900,
    messages: [
      { role: "system", content: systemPrompt },
      {
        role: "user",
        content: `Location: ${city || "Unknown"}
Symptoms: ${symptoms.slice(0, 1200)}

Give safe, patient-friendly health guidance with do and don't advice. Include suitable OTC medicine options when appropriate, but do not prescribe.`
      }
    ]
  });

  return {
    isEmergency,
    specialty,
    advice: advice || "No advice returned."
  };
}

export async function analyzeReport({ reportText, reportType, patientContext, mode }) {
  if (!reportText || reportText.trim().length < 20) {
    return "The extracted report text is too short. Upload a clearer file or paste the report text.";
  }

  const prompt =
    mode === "imaging"
      ? `As a medical assistant, explain this imaging report or user-provided finding.
Type: ${reportType || "Medical imaging"}
Findings/context: ${(patientContext || reportText).slice(0, 1200)}

Provide:
1. Summary
2. What the finding may suggest
3. When to contact a doctor urgently
4. Suggested next steps

Do not diagnose from image pixels. Do not prescribe medicines.`
      : `Explain this ${reportType || "health report"} in simple terms.
Context: ${(patientContext || "None").slice(0, 300)}

Report:
${reportText.slice(0, 3500)}

Provide:
1. Summary
2. Key findings
3. When to see a doctor

Do not diagnose. Recommend clinician confirmation.`;

  const analysis = await createChatCompletion({
    temperature: 0.2,
    max_tokens: 700,
    messages: [{ role: "user", content: prompt }]
  });

  return analysis || "No analysis returned.";
}
