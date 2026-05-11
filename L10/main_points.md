Showcase how to port a traditional Vanilla HTML/JS/CSS frontend to a modern component-based architecture using Svelte.

1. Svelte Project Setup

- Replace the existing `frontend` static folder with a modern Svelte/Svite project.
- Explain the role of a bundler (Vite) and the development server compared to serving raw HTML files.

2. Component Architecture

- Break down the traditional monolithic `index.html` into smaller, reusable `.svelte` components (e.g., `Header.svelte`, `Menu.svelte`, `ReservationForm.svelte`).
- Detail the anatomy of a Svelte component: `<script>`, markup, and `<style>`.

3. State Management & Reactivity

- Replace manual DOM manipulation (e.g., `document.getElementById`, `innerHTML`) with Svelte's reactive state variables (`let menuItems = []`).
- Use two-way data binding on the reservation form via `bind:value` instead of manually querying input values on submission.
- Use Svelte's template logic blocks (`{#each}`, `{#if}`) to render the menu dynamically.

4. Data Fetching & API Integration

- Migrate vanilla `fetch` calls to integrate with the FastAPI backend.
- Introduce the `onMount` lifecycle hook to fetch the menu data when the component initializes.

5. Scoped Styling

- Port the global `style.css` into the relevant Svelte components.
- Explain how Svelte scopes styles locally to each component, preventing CSS bleed and making the design easier to maintain.
