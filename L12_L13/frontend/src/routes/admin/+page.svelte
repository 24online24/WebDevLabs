<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import {
		createMenuItem,
		deleteMenuItem,
		fetchMenuItems,
		getApiErrorMessage,
		updateMenuItem
	} from '$lib/api';
	import { authState } from '$lib/auth.svelte';
	import StaffManagementPanel from '$lib/components/StaffManagementPanel.svelte';
	import type { MenuItem, MenuItemPayload } from '$lib/types';

	let isReady = $state(false);
	let isLoadingItems = $state(true);
	let isSaving = $state(false);
	let deletingItemId = $state<number | null>(null);
	let accessMessage = $state('');
	let pageMessage = $state('');
	let pageMessageType = $state<'success' | 'error' | ''>('');
	let menuItems = $state<MenuItem[]>([]);
	let editingItemId = $state<number | null>(null);
	let name = $state('');
	let category = $state('');
	let price = $state('');
	let description = $state('');
	let image = $state('');
	let alt = $state('');
	let isFeatured = $state(false);

	function setPageMessage(message: string, type: 'success' | 'error'): void {
		pageMessage = message;
		pageMessageType = type;
	}

	function resetForm(): void {
		editingItemId = null;
		name = '';
		category = '';
		price = '';
		description = '';
		image = '';
		alt = '';
		isFeatured = false;
	}

	function startEditing(item: MenuItem): void {
		editingItemId = item.id;
		name = item.name;
		category = item.category;
		price = item.price.toFixed(2);
		description = item.description;
		image = item.image;
		alt = item.alt;
		isFeatured = item.isFeatured;
		pageMessage = '';
		pageMessageType = '';
	}

	function buildPayload(): MenuItemPayload {
		const parsedPrice = Number.parseFloat(price);

		if (!name.trim() || !category.trim() || !description.trim() || !image.trim() || !alt.trim()) {
			throw new Error('Complete every menu field before saving.');
		}

		if (Number.isNaN(parsedPrice) || parsedPrice <= 0) {
			throw new Error('Price must be a valid amount greater than 0.');
		}

		return {
			name: name.trim(),
			category: category.trim(),
			price: parsedPrice,
			description: description.trim(),
			image: image.trim(),
			alt: alt.trim(),
			isFeatured
		};
	}

	async function loadMenuItems(): Promise<void> {
		isLoadingItems = true;

		try {
			menuItems = await fetchMenuItems();
		} catch (error) {
			menuItems = [];
			setPageMessage(getApiErrorMessage(error, 'Unable to load menu items right now.'), 'error');
		} finally {
			isLoadingItems = false;
		}
	}

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
		await loadMenuItems();
	});

	async function handleSubmit(event: SubmitEvent): Promise<void> {
		event.preventDefault();

		if (!authState.sessionToken) {
			await goto('/login');
			return;
		}

		isSaving = true;
		pageMessage = '';
		pageMessageType = '';

		try {
			const payload = buildPayload();
			if (editingItemId === null) {
				const createdItem = await createMenuItem(authState.sessionToken, payload);
				menuItems = [...menuItems, createdItem].sort((left, right) => left.id - right.id);
				setPageMessage(`Added ${createdItem.name} to the catalog.`, 'success');
			} else {
				const updatedItem = await updateMenuItem(authState.sessionToken, editingItemId, payload);
				menuItems = menuItems.map((item) => (item.id === editingItemId ? updatedItem : item));
				setPageMessage(`Updated ${updatedItem.name}.`, 'success');
			}

			resetForm();
		} catch (error) {
			const fallbackMessage =
				error instanceof Error ? error.message : 'Unable to save the menu item right now.';
			setPageMessage(getApiErrorMessage(error, fallbackMessage), 'error');
		} finally {
			isSaving = false;
		}
	}

	async function handleDelete(item: MenuItem): Promise<void> {
		if (!authState.sessionToken) {
			await goto('/login');
			return;
		}

		const shouldDelete = window.confirm(`Delete ${item.name} from the catalog?`);
		if (!shouldDelete) {
			return;
		}

		deletingItemId = item.id;
		pageMessage = '';
		pageMessageType = '';

		try {
			await deleteMenuItem(authState.sessionToken, item.id);
			menuItems = menuItems.filter((menuItem) => menuItem.id !== item.id);
			if (editingItemId === item.id) {
				resetForm();
			}
			setPageMessage(`Deleted ${item.name}.`, 'success');
		} catch (error) {
			setPageMessage(
				getApiErrorMessage(error, 'Unable to delete the menu item right now.'),
				'error'
			);
		} finally {
			deletingItemId = null;
		}
	}

	async function handleLogout(): Promise<void> {
		await authState.logout();
		await goto('/login');
	}

	function formatPrice(priceValue: number): string {
		return `$${priceValue.toFixed(2)}`;
	}
</script>

<svelte:head>
	<title>Admin Dashboard</title>
</svelte:head>

<section class="dashboard-shell">
	{#if !isReady}
		<p class="loading-copy">Loading dashboard...</p>
	{:else if accessMessage}
		<div class="panel">
			<h1>Admin Dashboard</h1>
			<p>{accessMessage}</p>
			<a href="/manager">Go to manager dashboard</a>
		</div>
	{:else}
		<div class="dashboard-grid">
			<section class="panel hero-panel">
				<p class="eyebrow">Admin</p>
				<h1>Catalog control center</h1>
				<p class="intro">
					Signed in as {authState.currentUser?.display_name}. Add new dishes and drinks, revise
					descriptions, spotlight featured items, and keep the public menu synchronized with the
					backend catalog.
				</p>
				<div class="actions">
					<a href="/manager">Open reservations view</a>
					<button type="button" onclick={handleLogout}>Log out</button>
				</div>
			</section>

			<section class="panel editor-panel">
				<div class="panel-header">
					<div>
						<p class="eyebrow">Editor</p>
						<h2>{editingItemId === null ? 'Add a menu item' : 'Edit menu item'}</h2>
					</div>
					{#if editingItemId !== null}
						<button class="ghost" type="button" onclick={resetForm}>Create new item</button>
					{/if}
				</div>

				<form class="editor-form" onsubmit={handleSubmit}>
					<label>
						<span>Name</span>
						<input bind:value={name} type="text" required />
					</label>

					<label>
						<span>Category</span>
						<input bind:value={category} type="text" required />
					</label>

					<label>
						<span>Price</span>
						<input bind:value={price} type="number" min="0.01" step="0.01" required />
					</label>

					<label class="field-span-2">
						<span>Description</span>
						<textarea bind:value={description} rows="4" required></textarea>
					</label>

					<label class="field-span-2">
						<span>Image URL</span>
						<input bind:value={image} type="url" required />
					</label>

					<label class="field-span-2">
						<span>Image alt text</span>
						<input bind:value={alt} type="text" required />
					</label>

					<label class="checkbox-field field-span-2">
						<input bind:checked={isFeatured} type="checkbox" />
						<span>Mark as featured on the public menu</span>
					</label>

					<div class="form-actions field-span-2">
						<button type="submit" disabled={isSaving}>
							{isSaving
								? editingItemId === null
									? 'Adding item...'
									: 'Saving changes...'
								: editingItemId === null
									? 'Add item'
									: 'Save changes'}
						</button>
						<button class="secondary" type="button" onclick={resetForm} disabled={isSaving}>
							Reset form
						</button>
					</div>
				</form>

				{#if pageMessage}
					<p class={`message ${pageMessageType}`}>{pageMessage}</p>
				{/if}
			</section>

			<section class="panel inventory-panel">
				<div class="panel-header">
					<div>
						<p class="eyebrow">Inventory</p>
						<h2>Published catalog</h2>
					</div>
					<p class="inventory-count">{menuItems.length} items</p>
				</div>

				{#if isLoadingItems}
					<p class="loading-copy">Loading menu items...</p>
				{:else if menuItems.length === 0}
					<p class="empty-state">No menu items found. Add one to publish it.</p>
				{:else}
					<div class="inventory-grid">
						{#each menuItems as item (item.id)}
							<article class="catalog-card">
								<img src={item.image} alt={item.alt} loading="lazy" />
								<div class="card-body">
									<div class="card-topline">
										<div>
											<p class="category-label">{item.category}</p>
											<h3>{item.name}</h3>
										</div>
										<p class="price-tag">{formatPrice(item.price)}</p>
									</div>

									<p class="description">{item.description}</p>

									<div class="badge-row">
										{#if item.isFeatured}
											<span class="badge featured">Featured</span>
										{/if}
										<span class="badge">ID #{item.id}</span>
									</div>

									<div class="card-actions">
										<button type="button" onclick={() => startEditing(item)}>Edit</button>
										<button
											type="button"
											class="danger"
											onclick={() => handleDelete(item)}
											disabled={deletingItemId === item.id}
										>
											{deletingItemId === item.id ? 'Deleting...' : 'Delete'}
										</button>
									</div>
								</div>
							</article>
						{/each}
					</div>
				{/if}
			</section>

			<StaffManagementPanel />
		</div>
	{/if}
</section>

<style>
	.dashboard-shell {
		min-height: 100vh;
		padding: 24px;
		background:
			radial-gradient(circle at top right, rgba(214, 151, 81, 0.22), transparent 28%),
			linear-gradient(160deg, #f5eee7 0%, #f5eee7 36%, #2d1b16 36%, #2d1b16 100%);
	}

	.dashboard-grid {
		width: min(1180px, 100%);
		margin: 0 auto;
		display: grid;
		gap: 20px;
	}

	.panel {
		padding: 32px;
		border-radius: 24px;
		background: rgba(255, 250, 245, 0.95);
		box-shadow: 0 24px 60px rgba(31, 19, 15, 0.2);
	}

	.hero-panel {
		display: grid;
		gap: 12px;
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

	h2,
	h3 {
		margin: 0;
		font-family: 'Playfair Display', serif;
	}

	p {
		line-height: 1.6;
		color: #4f3b34;
	}

	.intro {
		margin: 0;
		max-width: 64ch;
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

	button:disabled {
		opacity: 0.6;
		cursor: wait;
	}

	.editor-form {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 16px;
	}

	label {
		display: grid;
		gap: 8px;
		font-weight: 700;
		color: #5a3e34;
	}

	span {
		font-size: 0.95rem;
	}

	input,
	textarea {
		border: 1px solid rgba(45, 27, 22, 0.14);
		border-radius: 16px;
		padding: 12px 14px;
		font: inherit;
		background: #fffdfb;
		color: #2d1b16;
	}

	textarea {
		resize: vertical;
		min-height: 120px;
	}

	.field-span-2 {
		grid-column: 1 / -1;
	}

	.checkbox-field {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.checkbox-field input {
		width: 18px;
		height: 18px;
		padding: 0;
		margin: 0;
	}

	.form-actions,
	.card-actions {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
	}

	.secondary {
		background: #ead8ca;
		color: #5a3e34;
	}

	.ghost {
		background: transparent;
		border: 1px solid rgba(138, 75, 8, 0.2);
		color: #8a4b08;
	}

	.danger {
		background: #8f2c2c;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		gap: 16px;
		align-items: end;
		margin-bottom: 20px;
	}

	.inventory-count,
	.loading-copy,
	.empty-state {
		margin: 0;
	}

	.inventory-count {
		font-weight: 800;
		color: #8a4b08;
	}

	.message {
		margin-top: 18px;
		padding: 12px 14px;
		border-radius: 14px;
		font-weight: 700;
	}

	.message.success {
		background: rgba(59, 122, 90, 0.14);
		color: #295940;
	}

	.message.error {
		background: rgba(143, 44, 44, 0.12);
		color: #8f2c2c;
	}

	.inventory-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 18px;
	}

	.catalog-card {
		border-radius: 24px;
		overflow: hidden;
		background: linear-gradient(180deg, rgba(255, 247, 241, 0.96), rgba(255, 255, 255, 0.98));
		border: 1px solid rgba(45, 27, 22, 0.08);
		box-shadow: 0 18px 40px rgba(45, 27, 22, 0.08);
	}

	img {
		display: block;
		width: 100%;
		height: 200px;
		object-fit: cover;
	}

	.card-body {
		padding: 18px;
		display: grid;
		gap: 14px;
	}

	.card-topline {
		display: flex;
		justify-content: space-between;
		gap: 14px;
		align-items: start;
	}

	.category-label,
	.description {
		margin: 0;
	}

	.category-label {
		font-size: 0.82rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: #8a4b08;
	}

	.price-tag {
		margin: 0;
		font-weight: 800;
		color: #8a4b08;
	}

	.description {
		color: #5e463e;
	}

	.badge-row {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
	}

	.badge {
		display: inline-flex;
		align-items: center;
		padding: 7px 10px;
		border-radius: 999px;
		background: rgba(138, 75, 8, 0.1);
		color: #7a4612;
		font-size: 0.85rem;
		font-weight: 700;
	}

	.badge.featured {
		background: rgba(214, 151, 81, 0.2);
		color: #8a4b08;
	}

	@media (max-width: 720px) {
		.dashboard-shell {
			padding: 18px;
		}

		.panel {
			padding: 24px;
		}

		.editor-form {
			grid-template-columns: 1fr;
		}

		.field-span-2 {
			grid-column: auto;
		}

		.panel-header,
		.card-topline {
			flex-direction: column;
			align-items: start;
		}

		.checkbox-field {
			align-items: start;
		}
	}
</style>
