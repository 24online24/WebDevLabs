# Bean & Brew Frontend

This is the Svelte frontend for the L10 Bean & Brew project. It talks to the FastAPI backend running in `../backend`.

## Run the project locally

1. Install the frontend dependencies from `L10/frontend`:

```sh
npm install
```

2. Start the backend from `L10/backend`:

```sh
uvicorn main:app --reload
```

3. Start the frontend from `L10/frontend`:

```sh
npm run dev
```

4. Open the app in your browser at the URL shown by Vite, usually `http://localhost:5173`.

## How the frontend reaches the API

The Svelte app sends requests directly to `http://127.0.0.1:8000/api`.

The FastAPI backend includes CORS settings for Svelte's default development and preview ports so the browser will allow those requests.

## Useful commands

```sh
npm run check
npm run build
npm run preview
```
