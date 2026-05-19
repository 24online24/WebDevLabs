<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authState } from '$lib/auth.svelte';

	let isReady = $state(false);

	onMount(async () => {
		await authState.hydrate();
		if (!authState.currentUser) {
			await goto('/login');
			return;
		}

		isReady = true;
	});

	async function handleLogout(): Promise<void> {
		await authState.logout();
		await goto('/login');
	}
</script>

<svelte:head>
	<title>Manager Dashboard</title>
</svelte:head>

<section class="dashboard-shell">
	{#if !isReady}
		<p>Loading dashboard...</p>
	{:else}
		<div class="panel">
			<p class="eyebrow">Manager</p>
			<h1>Reservation workflow hub</h1>
			<p>
				Signed in as {authState.currentUser?.display_name}. Reservation lists, status updates, and
				internal notes are the next screens to wire into this dashboard.
			</p>
			<div class="actions">
				{#if authState.currentUser?.role === 'admin'}
					<a href="/admin">Open admin dashboard</a>
				{/if}
				<button type="button" onclick={handleLogout}>Log out</button>
			</div>
		</div>
	{/if}
</section>

<style>
	:global(body) {
		margin: 0;
		font-family: 'Nunito', sans-serif;
		background: linear-gradient(180deg, #203b35 0%, #203b35 40%, #f3f1ea 40%, #f3f1ea 100%);
	}

	.dashboard-shell {
		min-height: 100vh;
		display: grid;
		place-items: center;
		padding: 24px;
	}

	.panel {
		width: min(100%, 720px);
		padding: 32px;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.94);
		box-shadow: 0 24px 60px rgba(23, 37, 35, 0.18);
	}

	.eyebrow {
		margin: 0 0 10px;
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: #2e6e5f;
	}

	h1 {
		margin: 0 0 12px;
		font-family: 'Playfair Display', serif;
		font-size: clamp(2rem, 4vw, 3rem);
	}

	p {
		line-height: 1.6;
		color: #35514a;
	}

	.actions {
		display: flex;
		gap: 14px;
		margin-top: 24px;
		flex-wrap: wrap;
	}

	a,
	button {
		border: none;
		border-radius: 999px;
		padding: 12px 18px;
		font: inherit;
		font-weight: 800;
		text-decoration: none;
		background: #2e6e5f;
		color: #f6fbfa;
		cursor: pointer;
	}

	a {
		display: inline-flex;
		align-items: center;
	}
</style>
