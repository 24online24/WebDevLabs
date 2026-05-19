<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authState } from '$lib/auth.svelte';
	import { getApiErrorMessage } from '$lib/api';
	import type { UserRole } from '$lib/types';

	let email = $state('');
	let password = $state('');
	let errorMessage = $state('');

	function getDashboardPath(role: UserRole): string {
		return role === 'admin' ? '/admin' : '/manager';
	}

	onMount(async () => {
		await authState.hydrate();
		if (authState.currentUser) {
			await goto(getDashboardPath(authState.currentUser.role));
		}
	});

	async function handleSubmit(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		errorMessage = '';

		try {
			const user = await authState.login({ email, password });
			await goto(getDashboardPath(user.role));
		} catch (error) {
			errorMessage = getApiErrorMessage(error, 'Unable to sign in right now.');
		}
	}
</script>

<svelte:head>
	<title>Staff Login</title>
</svelte:head>

<section class="login-shell">
	<div class="login-card">
		<p class="eyebrow">Staff Access</p>
		<h1>Sign in to the operations dashboard</h1>
		<p class="intro">
			Managers can review reservations. Admins can manage reservations, menu items, and staff
			accounts.
		</p>

		<form class="login-form" onsubmit={handleSubmit}>
			<label>
				<span>Email</span>
				<input bind:value={email} type="email" name="email" autocomplete="email" required />
			</label>

			<label>
				<span>Password</span>
				<input
					bind:value={password}
					type="password"
					name="password"
					autocomplete="current-password"
					required
				/>
			</label>

			{#if errorMessage}
				<p class="message error">{errorMessage}</p>
			{/if}

			<button type="submit" disabled={authState.isLoading}>
				{authState.isLoading ? 'Signing in...' : 'Sign in'}
			</button>
		</form>

		<a class="back-link" href="/">Back to the public site</a>
	</div>
</section>

<style>
	.login-shell {
		min-height: 100vh;
		display: grid;
		place-items: center;
		padding: 32px 20px;
		background:
			radial-gradient(circle at top, rgba(255, 214, 153, 0.55), transparent 30%),
			linear-gradient(180deg, #1f130f 0%, #2d1b16 45%, #f7efe7 45%, #f7efe7 100%);
	}

	.login-card {
		width: min(100%, 460px);
		padding: 32px;
		border-radius: 24px;
		background: rgba(255, 250, 245, 0.96);
		box-shadow: 0 24px 60px rgba(31, 19, 15, 0.22);
	}

	.eyebrow {
		margin: 0 0 10px;
		text-transform: uppercase;
		letter-spacing: 0.18em;
		font-size: 0.75rem;
		font-weight: 700;
		color: #8a4b08;
	}

	h1 {
		margin: 0;
		font-family: 'Playfair Display', serif;
		font-size: clamp(2rem, 5vw, 2.7rem);
		line-height: 1.1;
	}

	.intro {
		margin: 14px 0 24px;
		color: #5c4138;
		line-height: 1.6;
	}

	.login-form {
		display: grid;
		gap: 16px;
	}

	label {
		display: grid;
		gap: 8px;
		font-weight: 700;
	}

	span {
		font-size: 0.95rem;
	}

	input {
		border: 1px solid rgba(45, 27, 22, 0.14);
		border-radius: 14px;
		padding: 14px 16px;
		font: inherit;
		background: #fff;
	}

	button {
		border: none;
		border-radius: 999px;
		padding: 14px 18px;
		font: inherit;
		font-weight: 800;
		background: linear-gradient(135deg, #8a4b08, #d17d14);
		color: #fffaf5;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.65;
		cursor: wait;
	}

	.message {
		margin: 0;
		padding: 12px 14px;
		border-radius: 12px;
		font-weight: 700;
	}

	.error {
		background: rgba(183, 28, 28, 0.12);
		color: #8f1d1d;
	}

	.back-link {
		display: inline-block;
		margin-top: 18px;
		color: #8a4b08;
		font-weight: 700;
		text-decoration: none;
	}

	@media (max-width: 640px) {
		.login-card {
			padding: 24px;
		}
	}
</style>
