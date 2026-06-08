# dataroots QnA Bot

Question-answering bot over the dataroots Notion doc, built for Day 1 of the
Agentic AI Academy. Single self-contained Modal app: Gemini 2.5 Flash-Lite for
answers, headless Chromium for scraping, and a small branded web UI.

## How it works

1. **Scrape once, at build time.** A headless Chromium crawl of the Notion doc
   and its subpages runs while the container image is built, and the resulting
   text is baked into the image (`/kb.txt`). Requests never scrape live, so they
   stay fast and deterministic. The brief guarantees the pages and URLs won't
   change, so a one-time scrape is safe.
2. **Grounded answers.** The full knowledge base fits in Gemini's context
   window, so it is passed in the prompt. A strict system instruction plus
   `temperature=0` keep answers grounded in the doc. When the answer isn't in
   the knowledge base, the bot returns a fixed fallback instead of guessing.
3. **Two endpoints in one app.** `answer` is the JSON contract endpoint
   (`GET ?query=... -> {"answer": ...}`). `web` serves a branded UI and calls
   its own `/ask` route, so the page and its API share one origin (no CORS).

## Run it

```bash
# one-time: store the Gemini key as a Modal secret
modal secret create gemini GEMINI_API_KEY=<your-key>

# deploy (first deploy builds the image and runs the scrape)
modal deploy qna_bot.py
```

## Try it

```bash
curl --get --data-urlencode "query=What is dataroots?" <answer-endpoint-url>
```

## Stack

Python, Modal (serverless hosting), Selenium + headless Chromium (scraping),
Google Gemini 2.5 Flash-Lite (LLM), FastAPI (web UI).
