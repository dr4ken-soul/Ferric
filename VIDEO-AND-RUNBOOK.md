# Ferric Video And Demo Runbook

This is the shortest path for running Ferric and making the submission video.

## Two Different Meanings Of Record

There are two separate actions. They are not the same thing.

**Ferric captures model traffic.** The button on the site sends one prompt to Groq and stores the request and response as a JSON cassette. It does not record your screen, create a video or return a video file.

**You record the submission video.** Use a screen recorder such as Windows Snipping Tool, Xbox Game Bar or OBS. That video shows you using Ferric. Ferric does not create this video for you.

## What The Demo Does

The live demo has one server-side action and one browser-local action.

1. `Capture with Groq` sends the prompt to `/api/ferric`. The server calls Groq with `GROQ_API_KEY`, normalises the request and response into a cassette, redacts known secret forms, and returns the cassette to the browser.
2. `Replay captured response` reads the stored response from that cassette in the browser. It does not call Groq and does not open a second network request to the provider.

There is no database. The cassette exists for the current browser session. That keeps the hosted demo small and avoids storing visitor prompts. The Python package remains the durable local and CI tool for real project cassettes.

## Local Run

The local browser demo needs Node.js 18 or later and a Groq key.

From the repository root, add your key to the ignored `.env` file:

```dotenv
GROQ_API_KEY=gsk_your-key-here
```

The default hosted model is `qwen/qwen3.6-27b`. It is taken from the model access list for this Groq account. To override it locally, add `FERRIC_DEMO_MODEL` to `.env`.

Then run:

```powershell
npm --prefix web ci
npm run dev
```

Open <http://localhost:5173>. The Vite server supplies the page and the `/api/ferric` demo endpoint together. No Python command is needed for this browser demo.

## Vercel Run

Create a Vercel project from the repository and use `web` as the Root Directory.

Set these values:

```text
Framework Preset: Vite
Install Command: npm ci
Build Command: npm run build:vercel
Output Directory: dist
```

In Vercel Project Settings, open Environment Variables and add:

```text
Name: GROQ_API_KEY
Value: your Groq key
Environment: Production, Preview, and Development
```

The demo uses `qwen/qwen3.6-27b` by default. You can optionally add `FERRIC_DEMO_MODEL` in Vercel if your Groq account later exposes a different chat model.

Redeploy after adding the variable. The key is read only by the serverless function. It is never sent to the browser bundle.

## Make The Silent Screen Video

Start Windows Snipping Tool screen recording, Xbox Game Bar or OBS before the first step below. Use a plain screen recording with no voiceover, captions or slides. Ferric does not generate the video file.

1. Open the deployed site.
2. Scroll to `LIVE RECORDER`.
3. Leave the example prompt visible so the action is easy to follow.
4. Click `Capture with Groq`.
5. Wait for the cassette ID, event rows and assistant response to appear.
6. Point at the cassette ID and redaction count briefly.
7. Click `Replay captured response`.
8. Show the status line stating that Groq was not called.
9. Scroll through the recorder, assertion panels, cassette anatomy and docs.
10. Finish on the install commands and the GitHub link.

Keep the browser network panel open if you want the replay proof to be visible. The capture action shows one request to `/api/ferric`. The replay action changes the response from the cassette without another provider request.

## What The Video Proves

- A real Groq response enters a Ferric cassette.
- The cassette is readable in the browser.
- The response can be replayed without another provider call.
- The product still has an offline Python test suite and CLI for CI use.

The live demo is a hosted demonstration path. It does not replace the committed cassette library or the Python replay engine.
