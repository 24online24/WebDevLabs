<!--
	Profile.svelte
	Demonstrates passing data from parent to child using the `$props` rune.
	The parent renders this component with attributes like:
		<Profile name="Alice" city="Paris" />
	and those values flow down into the child as props.
-->

<script lang="ts">
	let { name, city, age, description } = $props<{
		name: string;
		city: string;
		age: number;
		description: string;
	}>();

	const age_in_months = $derived(age * 12);
	const image_url = $derived(
		`https://picsum.photos/seed/${encodeURIComponent(`${name}-${city}-${age}`)}/96`
	);
</script>

<article class="profile">
	<div class="header">
		<img class="avatar" src={image_url} alt={`Profile photo for ${name}`} />
		<div>
			<h3>
				{name}
				<span class="age">{age} years/</span>
				<span class="age">{age_in_months} months old</span>
			</h3>
			<p>Lives in <em>{city}</em></p>
		</div>
	</div>

	<details class="description">
		<summary>View description</summary>
		<p>{description}</p>
	</details>
</article>

<style>
	.profile {
		padding: 0.75rem 1rem;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		background: #f1f5f9;
	}

	.header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.avatar {
		width: 56px;
		height: 56px;
		border-radius: 999px;
		object-fit: cover;
		flex-shrink: 0;
		border: 2px solid #fff;
		box-shadow: 0 0 0 1px #cbd5e1;
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

	.description {
		margin-top: 0.75rem;
	}

	summary {
		cursor: pointer;
		font-weight: 600;
		color: #0f172a;
	}

	.description p {
		margin-top: 0.5rem;
		line-height: 1.5;
	}
</style>
