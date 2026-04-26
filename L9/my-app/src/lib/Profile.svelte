<!--
	Profile.svelte
	Demonstrates passing data from parent to child using the `$props` rune.
	The parent renders this component with attributes like:
		<Profile name="Alice" city="Paris" />
	and those values flow down into the child as props.
-->

<script lang="ts">
	let { name, city } = $props<{ name: string; city: string }>();
</script>

<article class="profile">
	<h3>{name}</h3>
	<p>Lives in <em>{city}</em></p>
</article>

<style>
	.profile {
		padding: 0.75rem 1rem;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		background: #f1f5f9;
	}

	h3 {
		margin: 0 0 0.25rem;
		color: #0f172a;
	}

	p {
		margin: 0;
		color: #475569;
	}

	em {
		color: #ff3e00;
		font-style: normal;
		font-weight: 600;
	}
</style>
