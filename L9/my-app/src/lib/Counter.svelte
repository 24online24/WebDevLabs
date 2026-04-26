<!--
	Counter.svelte
	Demonstrates reactivity and event handling in Svelte 5:
	- `$state` rune to declare reactive state.
	- `onclick` event handler to mutate the state.
	The UI re-renders automatically whenever `count` changes — no manual
	DOM manipulation (querySelector / innerHTML) required.
-->

<script lang="ts">
	let count = $state(0);

	function increment() {
		count += 1;
	}

	function reset() {
		count = 0;
	}
</script>

<section class="counter">
	<h2>Interactive Counter</h2>
	<p>Current count: <strong>{count}</strong></p>

	<div class="actions">
		<button onclick={increment}>Increment</button>
		<button onclick={reset} class="secondary">Reset</button>
	</div>
</section>

<style>
	.counter {
		padding: 1rem 1.25rem;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		background: #ffffff;
	}

	h2 {
		margin: 0 0 0.5rem;
		color: #ff3e00;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.75rem;
	}

	button {
		padding: 0.4rem 0.9rem;
		border: 1px solid #ff3e00;
		border-radius: 6px;
		background: #ff3e00;
		color: white;
		cursor: pointer;
		font-weight: 600;
	}

	button.secondary {
		background: white;
		color: #ff3e00;
	}

	button:hover {
		filter: brightness(0.95);
	}
</style>
