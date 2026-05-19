# AI Doctor Web

Full-stack web version of the original Streamlit app.

## Stack

- React + Vite frontend
- Node.js + Express API
- Groq for AI guidance
- OpenStreetMap/Nominatim/Overpass for city and hospital search

## Run

```bash
npm install
npm run build
npm start
```

On Windows PowerShell, you can also run:

```powershell
.\start-server.ps1
```

Create a `.env` file from `.env.example` and set `GROQ_API_KEY` for live AI responses.

The app and API run together on `http://127.0.0.1:5050`.

`npm run dev` is also available for a split Vite + API workflow, but the production-style start command is the most reliable option on Windows/OneDrive workspaces.

## Deploy on Netlify

This project includes `netlify.toml`, so you can deploy the React frontend and API routes from the `website` folder. Netlify Functions handle `/api/...` routes in production.

Netlify settings:

```text
Base directory: website
Build command: npm run build
Publish directory: client/dist
Functions directory: netlify/functions
```

Set this Netlify environment variable for live AI responses:

```text
GROQ_API_KEY=your_groq_api_key_here
```

Leave `VITE_API_BASE` unset on Netlify so the frontend uses same-origin `/api/...` routes. For local development, keep `VITE_API_BASE=http://127.0.0.1:5050` in `.env`.
