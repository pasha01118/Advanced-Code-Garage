import { createHash, timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const GEMINI_MODEL = process.env.GEMINI_MODEL || "gemini-3.6-flash";
const GEMINI_ENDPOINT =
  "https://generativelanguage.googleapis.com/v1beta/models/" +
  GEMINI_MODEL +
  ":generateContent";
const MAX_PROMPT_LENGTH = 12000;

function tokensEqual(a: string, b: string): boolean {
  const aHash = createHash("sha256").update(a).digest();
  const bHash = createHash("sha256").update(b).digest();
  return timingSafeEqual(aHash, bHash);
}

export async function POST(request: Request) {
  const proxyTokens = [
    process.env.GOOGLE_AI_STUDIO_PROXY_TOKEN,
    process.env.GOOGLE_AI_PROXY_TOKEN,
  ].filter((token): token is string => Boolean(token));
  if (proxyTokens.length === 0) {
    return NextResponse.json({ error: "proxy not configured" }, { status: 503 });
  }

  const auth = request.headers.get("authorization") ?? "";
  const providedToken = auth.startsWith("Bearer ") ? auth.slice("Bearer ".length) : "";
  const authorized = proxyTokens.map((token) => tokensEqual(providedToken, token)).some(Boolean);
  if (!authorized) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const apiKey = process.env.GOOGLE_AI_STUDIO_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "AI key not configured" }, { status: 503 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON" }, { status: 400 });
  }
  const prompt =
    typeof body === "object" && body !== null && "prompt" in body && typeof (body as { prompt?: unknown }).prompt === "string"
      ? (body as { prompt: string }).prompt.trim()
      : "";
  if (!prompt) {
    return NextResponse.json({ error: "empty prompt" }, { status: 400 });
  }
  if (prompt.length > MAX_PROMPT_LENGTH) {
    return NextResponse.json({ error: "prompt too long" }, { status: 400 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const res = await fetch(GEMINI_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey,
      },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.4, maxOutputTokens: 512 },
      }),
      signal: controller.signal,
    });
    if (!res.ok) {
      // Never reflect raw upstream bodies; they can contain secrets.
      return NextResponse.json({ error: "gemini upstream error", status: res.status }, { status: 502 });
    }
    const data = (await res.json()) as {
      candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
    };
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
    if (!text) {
      return NextResponse.json({ error: "empty completion" }, { status: 502 });
    }
    return NextResponse.json({ text });
  } catch {
    return NextResponse.json({ error: "gemini request failed" }, { status: 502 });
  } finally {
    clearTimeout(timer);
  }
}
