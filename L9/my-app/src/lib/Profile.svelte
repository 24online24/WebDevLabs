<!--
	Profile.svelte
	Demonstrates passing data from parent to child using the `$props` rune.
	The parent renders this component with attributes like:
		<Profile name="Alice" city="Paris" />
	and those values flow down into the child as props.
-->

<script lang="ts">
	let { name, city, age } = $props<{ name: string; city: string; age: number }>();
</script>

<article class="profile">
	<div>
		<h3>
			{name}
			<span class="age">{age} years/</span>
		</h3>
		<p>Lives in <em>{city}</em></p>
	</div>
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

	.age {
		font-size: 0.65rem;
		color: #64748b;
		opacity: 0.8;
		font-weight: 400;
		margin-left: 0.1rem;
	}
</style>
