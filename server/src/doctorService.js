import { browserHeaders } from "./config.js";
import { createChatCompletion } from "./llmClient.js";

function normalizeDoctor(name, specialty, city, source = "Search") {
  const query = encodeURIComponent(`${name} ${specialty} ${city}`);
  return {
    name,
    specialty,
    rating: "N/A",
    reviews: "",
    experience: "Experienced practitioner",
    fees: "Contact clinic",
    appointment: "Call to confirm",
    hospital: "Clinic or hospital",
    address: city,
    link: `https://www.google.com/search?q=${query}`,
    mapLink: `https://www.google.com/maps/search/${query}`,
    source
  };
}

export async function getDoctors(city = "", specialty = "General Physician") {
  const googleDoctors = await searchGoogleDoctors(city, specialty);
  if (googleDoctors.length >= 3) return googleDoctors;

  const aiDoctors = await getDoctorsFromGroq(city, specialty);
  return aiDoctors.length ? aiDoctors : fallbackDoctors(city, specialty);
}

async function searchGoogleDoctors(city, specialty) {
  const url = `https://www.google.com/search?q=${encodeURIComponent(`top ${specialty} doctor in ${city} India rating`)}&num=10`;

  try {
    const response = await fetch(url, { headers: browserHeaders });
    const html = await response.text();
    const matches = [...html.matchAll(/<h3[^>]*>(.*?)<\/h3>/gi)]
      .map((match) => match[1].replace(/<[^>]+>/g, "").trim())
      .filter((title) => /dr\.?|doctor|clinic|hospital/i.test(title))
      .slice(0, 6);

    return matches.map((title) => normalizeDoctor(title, specialty, city, "Google"));
  } catch {
    return [];
  }
}

async function getDoctorsFromGroq(city, specialty) {
  try {
    const text = await createChatCompletion({
      temperature: 0.25,
      max_tokens: 350,
      messages: [
        {
          role: "user",
          content: `List 4 INDIVIDUAL DOCTORS who are ${specialty} in ${city}, India. Do NOT list hospital names or clinic names.
Format every line as:
Doctor Name | Hospital/Clinic Where They Work | Rating | Consultation Fees

IMPORTANT: Focus on DOCTOR NAMES, not hospital names. Example:
Dr. Rajesh Kumar | Apollo Hospital | 4.5 | Rs. 500`
        }
      ]
    });

    return text
      .split("\n")
      .filter((line) => line.includes("|"))
      .slice(0, 4)
      .map((line) => {
        const [name, hospital, rating, fees] = line.split("|").map((part) => part.trim());
        const doctor = normalizeDoctor(name.replace(/^[-*\d. ]+/, ""), specialty, city, "AI Recommendation");
        return {
          ...doctor,
          hospital: hospital || doctor.hospital,
          rating: rating || doctor.rating,
          fees: fees || doctor.fees,
          reviews: "50+"
        };
      });
  } catch {
    return [];
  }
}

function fallbackDoctors(city, specialty) {
  return [
    normalizeDoctor(`${specialty} near ${city}`, specialty, city, "Maps"),
    normalizeDoctor(`Top ${specialty} clinics in ${city}`, specialty, city, "Maps"),
    normalizeDoctor(`Verified ${specialty} appointment ${city}`, specialty, city, "Search")
  ];
}
