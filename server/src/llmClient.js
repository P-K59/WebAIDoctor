import { groq, GROQ_MODEL, OLLAMA_CHAT_URL, OLLAMA_MODEL } from "./config.js";

const isNetlify = Boolean(process.env.NETLIFY);

function isGroqLimitError(error) {
  const text = String(error?.message || error || "").toLowerCase();
  return [
    "rate",
    "quota",
    "limit",
    "429",
    "too many requests",
    "rate_limit",
    "insufficient_quota"
  ].some((marker) => text.includes(marker));
}

async function createOllamaChatCompletion({ messages, temperature = 0.2, max_tokens = 512 }) {
  const response = await fetch(OLLAMA_CHAT_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      messages,
      stream: false,
      options: {
        temperature,
        num_predict: max_tokens
      }
    })
  });

  if (!response.ok) {
    throw new Error(`Ollama request failed: HTTP ${response.status}`);
  }

  const data = await response.json();
  return data?.message?.content?.trim() || "";
}

export async function createChatCompletion(options) {
  if (groq) {
    try {
      const response = await groq.chat.completions.create({
        model: GROQ_MODEL,
        ...options
      });
      return response.choices[0]?.message?.content || "";
    } catch (error) {
      if (!isGroqLimitError(error)) {
        throw new Error(`Groq request failed: ${error?.message || "Unknown error"}`);
      }
      if (isNetlify) {
        throw new Error("Groq API rate limit or quota was reached. Check the GROQ_API_KEY usage/billing in Groq.");
      }
    }
  }

  if (isNetlify) {
    throw new Error("GROQ_API_KEY is not configured for Netlify Functions.");
  }

  try {
    return await createOllamaChatCompletion(options);
  } catch (error) {
    throw new Error(`Local Ollama fallback failed: ${error?.message || "Unknown error"}`);
  }
}
