<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authState } from '$lib/auth.svelte';

	let isReady = $state(false);
	let accessMessage = $state('');

	onMount(async () => {
		await authState.hydrate();
		if (!authState.currentUser) {
			await goto('/login');
			return;
		}

		if (authState.currentUser.role !== 'admin') {
			accessMessage = 'This dashboard is reserved for admin accounts.';
			isReady = true;
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
	<title>Admin Dashboard</title>
</svelte:head>

<section class="dashboard-shell">
	{#if !isReady}
		<p>Loading dashboard...</p>
	{:else if accessMessage}
		<div class="panel">
			<h1>Admin Dashboard</h1>
			<p>{accessMessage}</p>
			<a href="/manager">Go to manager dashboard</a>
		</div>
	{:else}
		<div class="panel">
			<p class="eyebrow">Admin</p>
			<h1>Operations control center</h1>
			<p>
				Signed in as {authState.currentUser?.display_name}. Menu management, reservation tools, and
				staff account screens are the next UI slice to connect.
			</p>
			<div class="actions">
				<a href="/manager">Open reservations view</a>
				<button type="button" onclick={handleLogout}>Log out</button>
			</div>
		</div>
	{/if}
</section>

<style>
	:global(body) {
		margin: 0;
		font-family: 'Nunito', sans-serif;
		background: linear-gradient(160deg, #f5eee7 0%, #f5eee7 52%, #2d1b16 52%, #2d1b16 100%);
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
		background: rgba(255, 250, 245, 0.95);
		box-shadow: 0 24px 60px rgba(31, 19, 15, 0.2);
	}

	.eyebrow {
		margin: 0 0 10px;
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: #8a4b08;
	}

	h1 {
		margin: 0 0 12px;
		font-family: 'Playfair Display', serif;
		font-size: clamp(2rem, 4vw, 3rem);
	}

	p {
		line-height: 1.6;
		color: #4f3b34;
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
		background: #8a4b08;
		color: #fffaf5;
		cursor: pointer;
	}

	a {
		display: inline-flex;
		align-items: center;
	}

	button {
		background: #2d1b16;
	}
</style>
