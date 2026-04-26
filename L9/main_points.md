Introduce the general concept of a frontend framework and provide a simple, fundamental example using Svelte.

- Frontend concepts: Declarative UI, Component-based architecture.
- Svelte basics: `.svelte` file structure (script, markup, style), importing components.
- Reactivity and Data Flow: Runes (`$state`, `$props`), basic event handling (`onclick`).

1. General Frontend Framework Concepts

- What is a frontend framework and why it is used (moving away from manual DOM manipulation like `querySelector` and `innerHTML`).
- Introduction to Components: breaking down a web page into reusable, self-contained building blocks.

2. Svelte Basics and Component Structure

- The anatomy of a Svelte component: combining `<script>`, HTML markup, and scoped `<style>` in a single `.svelte` file.
- Create a basic component (`HelloWorld.svelte`) that renders a static HTML greeting.
- Introduce component composition: modify an `App.svelte` root component to import and render the `HelloWorld` component.

3. State, Events, and Props

- Introduce **Reactivity and Events**: Create an interactive button component. Use the `$state` rune (`let count = $state(0)`) to store data, and the `onclick` event listener to show how changing the state automatically updates the UI.
- Introduce **Props**: Modify a `Profile.svelte` component to accept dynamic data from its parent using the `$props` rune (`let { name, city } = $props()`). Show how the parent passes these attributes into the child component (e.g., `<Profile name="Alice" city="Paris" />`).
