<script lang="ts">
	import type { MenuItem } from '$lib/types';

	let { item }: { item: MenuItem } = $props();

	function formatPrice(price: number): string {
		return `$${price.toFixed(2)}`;
	}
</script>

<article class="menu-card">
	<img src={item.image} alt={item.alt} loading="lazy" />
	<div class="menu-card-body">
		<h3>{item.name}</h3>
		<p>{item.description}</p>
		<span class="price">{formatPrice(item.price)}</span>
	</div>
</article>

<style>
	.menu-card {
		background: var(--white);
		border-radius: var(--radius);
		overflow: hidden;
		box-shadow: var(--shadow);
		transition:
			transform var(--transition),
			box-shadow var(--transition);
	}

	.menu-card:hover {
		transform: translateY(-6px);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
	}

	img {
		width: 100%;
		height: 200px;
		object-fit: cover;
		display: block;
	}

	.menu-card-body {
		padding: 20px;
	}

	h3 {
		font-size: 1.2rem;
		color: var(--primary);
		margin-bottom: 6px;
	}

	p {
		font-size: 0.95rem;
		color: var(--text-light);
		margin-bottom: 12px;
	}

	.price {
		font-weight: 700;
		color: var(--accent);
		font-size: 1.1rem;
	}
</style>
