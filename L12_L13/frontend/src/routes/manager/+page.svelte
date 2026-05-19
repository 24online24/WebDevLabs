<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fetchReservations, getApiErrorMessage, updateReservation } from '$lib/api';
	import { authState } from '$lib/auth.svelte';
	import type { ReservationResponse, ReservationStatus } from '$lib/types';

	let isReady = $state(false);
	let isLoadingReservations = $state(true);
	let isSavingReservationId = $state<number | null>(null);
	let reservations = $state<ReservationResponse[]>([]);
	let selectedStatus = $state<'all' | ReservationStatus>('all');
	let selectedDate = $state('');
	let noteDrafts = $state<Record<number, string>>({});
	let pageMessage = $state('');
	let pageMessageType = $state<'success' | 'error' | ''>('');

	const statusOptions: Array<{ value: 'all' | ReservationStatus; label: string }> = [
		{ value: 'all', label: 'All statuses' },
		{ value: 'pending', label: 'Pending' },
		{ value: 'confirmed', label: 'Confirmed' },
		{ value: 'completed', label: 'Completed' },
		{ value: 'cancelled', label: 'Cancelled' }
	];

	function setPageMessage(message: string, type: 'success' | 'error'): void {
		pageMessage = message;
		pageMessageType = type;
	}

	function syncNoteDrafts(items: ReservationResponse[]): void {
		noteDrafts = Object.fromEntries(
			items.map((reservation) => [reservation.id, reservation.internal_notes ?? ''])
		);
	}

	function matchesActiveFilters(reservation: ReservationResponse): boolean {
		if (selectedStatus !== 'all' && reservation.status !== selectedStatus) {
			return false;
		}

		if (selectedDate && reservation.date !== selectedDate) {
			return false;
		}

		return true;
	}

	async function loadReservations(): Promise<void> {
		if (!authState.sessionToken) {
			return;
		}

		isLoadingReservations = true;
		pageMessage = '';
		pageMessageType = '';

		try {
			const items = await fetchReservations(authState.sessionToken, {
				date: selectedDate || undefined,
				status: selectedStatus === 'all' ? undefined : selectedStatus
			});
			reservations = items;
			syncNoteDrafts(items);
		} catch (error) {
			reservations = [];
			setPageMessage(getApiErrorMessage(error, 'Unable to load reservations right now.'), 'error');
		} finally {
			isLoadingReservations = false;
		}
	}

	function updateNoteDraft(reservationId: number, value: string): void {
		noteDrafts = {
			...noteDrafts,
			[reservationId]: value
		};
	}

	async function saveReservation(
		reservationId: number,
		payload: { status?: ReservationStatus; internal_notes?: string | null }
	): Promise<void> {
		if (!authState.sessionToken) {
			await goto('/login');
			return;
		}

		isSavingReservationId = reservationId;

		try {
			const updatedReservation = await updateReservation(
				authState.sessionToken,
				reservationId,
				payload
			);
			reservations = reservations
				.map((reservation) => (reservation.id === reservationId ? updatedReservation : reservation))
				.filter(matchesActiveFilters);
			updateNoteDraft(reservationId, updatedReservation.internal_notes ?? '');
			setPageMessage(`Reservation #${reservationId} updated.`, 'success');
		} catch (error) {
			setPageMessage(
				getApiErrorMessage(error, 'Unable to update the reservation right now.'),
				'error'
			);
		} finally {
			isSavingReservationId = null;
		}
	}

	async function handleStatusUpdate(
		reservationId: number,
		status: ReservationStatus
	): Promise<void> {
		const trimmedNotes = (noteDrafts[reservationId] ?? '').trim();
		await saveReservation(reservationId, {
			status,
			internal_notes: trimmedNotes || null
		});
	}

	async function handleNotesSave(reservationId: number): Promise<void> {
		const trimmedNotes = (noteDrafts[reservationId] ?? '').trim();
		await saveReservation(reservationId, {
			internal_notes: trimmedNotes || null
		});
	}

	async function handleFilterSubmit(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		await loadReservations();
	}

	async function clearFilters(): Promise<void> {
		selectedStatus = 'all';
		selectedDate = '';
		await loadReservations();
	}

	function formatReservationSlot(reservation: ReservationResponse): string {
		return `${reservation.date} at ${reservation.time.slice(0, 5)}`;
	}

	onMount(async () => {
		await authState.hydrate();
		if (!authState.currentUser) {
			await goto('/login');
			return;
		}

		isReady = true;
		await loadReservations();
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
		<p class="loading-copy">Loading dashboard...</p>
	{:else}
		<div class="dashboard-grid">
			<section class="panel hero-panel">
				<p class="eyebrow">Manager</p>
				<h1>Reservation workflow hub</h1>
				<p class="intro">
					Signed in as {authState.currentUser?.display_name}. Review incoming bookings, filter the
					day's service list, and keep notes synchronized with the backend.
				</p>
				<div class="actions">
					{#if authState.currentUser?.role === 'admin'}
						<a href="/admin">Open admin dashboard</a>
					{/if}
					<button type="button" onclick={handleLogout}>Log out</button>
				</div>
			</section>

			<section class="panel filters-panel">
				<form class="filters-form" onsubmit={handleFilterSubmit}>
					<label>
						<span>Status</span>
						<select bind:value={selectedStatus}>
							{#each statusOptions as option (option.value)}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</label>

					<label>
						<span>Date</span>
						<input bind:value={selectedDate} type="date" />
					</label>

					<div class="filter-actions">
						<button type="submit">Apply filters</button>
						<button class="secondary" type="button" onclick={clearFilters}>Clear</button>
					</div>
				</form>

				{#if pageMessage}
					<p class={`message ${pageMessageType}`}>{pageMessage}</p>
				{/if}
			</section>

			<section class="panel reservations-panel">
				<div class="panel-header">
					<div>
						<p class="eyebrow">Queue</p>
						<h2>Upcoming reservations</h2>
					</div>
					<p class="reservation-count">{reservations.length} loaded</p>
				</div>

				{#if isLoadingReservations}
					<p class="loading-copy">Loading reservations...</p>
				{:else if reservations.length === 0}
					<p class="empty-state">
						No reservations match the current filters. Try another date or clear the status filter.
					</p>
				{:else}
					<div class="reservation-list">
						{#each reservations as reservation (reservation.id)}
							<article class="reservation-card">
								<div class="reservation-summary">
									<div>
										<h3>{reservation.contact_name}</h3>
										<p>{reservation.contact_email}</p>
									</div>
									<span class={`status-pill ${reservation.status}`}>{reservation.status}</span>
								</div>

								<div class="reservation-meta">
									<p><strong>When:</strong> {formatReservationSlot(reservation)}</p>
									<p><strong>Guests:</strong> {reservation.guest_count}</p>
									<p>
										<strong>Request:</strong>
										{reservation.special_requests || 'No special requests submitted.'}
									</p>
								</div>

								<label class="notes-field">
									<span>Internal notes</span>
									<textarea
										rows="3"
										value={noteDrafts[reservation.id] ?? ''}
										oninput={(event) =>
											updateNoteDraft(
												reservation.id,
												(event.currentTarget as HTMLTextAreaElement).value
											)}
									></textarea>
								</label>

								<div class="card-actions">
									<button
										type="button"
										onclick={() => handleStatusUpdate(reservation.id, 'confirmed')}
										disabled={isSavingReservationId === reservation.id}
									>
										Confirm
									</button>
									<button
										type="button"
										class="secondary"
										onclick={() => handleStatusUpdate(reservation.id, 'completed')}
										disabled={isSavingReservationId === reservation.id}
									>
										Complete
									</button>
									<button
										type="button"
										class="danger"
										onclick={() => handleStatusUpdate(reservation.id, 'cancelled')}
										disabled={isSavingReservationId === reservation.id}
									>
										Cancel
									</button>
									<button
										type="button"
										class="ghost"
										onclick={() => handleNotesSave(reservation.id)}
										disabled={isSavingReservationId === reservation.id}
									>
										Save notes
									</button>
								</div>
							</article>
						{/each}
					</div>
				{/if}
			</section>
		</div>
	{/if}
</section>

<style>
	.dashboard-shell {
		min-height: 100vh;
		padding: 24px;
		background:
			radial-gradient(circle at top left, rgba(88, 153, 129, 0.18), transparent 28%),
			linear-gradient(180deg, #203b35 0%, #203b35 32%, #f3f1ea 32%, #f3f1ea 100%);
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
		background: rgba(255, 255, 255, 0.94);
		box-shadow: 0 24px 60px rgba(23, 37, 35, 0.18);
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
		color: #2e6e5f;
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
		color: #35514a;
	}

	.intro {
		margin: 0;
		max-width: 62ch;
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

	.filters-form {
		display: grid;
		gap: 16px;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		align-items: end;
	}

	label {
		display: grid;
		gap: 8px;
		font-weight: 700;
		color: #274740;
	}

	span {
		font-size: 0.95rem;
	}

	select,
	input,
	textarea {
		border: 1px solid rgba(32, 59, 53, 0.16);
		border-radius: 16px;
		padding: 12px 14px;
		font: inherit;
		background: #fff;
		color: #203b35;
	}

	textarea {
		resize: vertical;
		min-height: 92px;
	}

	.filter-actions {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
	}

	.secondary {
		background: #d5e5e0;
		color: #203b35;
	}

	.danger {
		background: #9d2f2f;
	}

	.ghost {
		background: transparent;
		border: 1px solid rgba(46, 110, 95, 0.24);
		color: #2e6e5f;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		gap: 16px;
		align-items: end;
		margin-bottom: 20px;
	}

	.reservation-count {
		margin: 0;
		font-weight: 800;
		color: #2e6e5f;
	}

	.reservation-list {
		display: grid;
		gap: 16px;
	}

	.reservation-card {
		padding: 22px;
		border-radius: 22px;
		background: linear-gradient(180deg, rgba(244, 248, 246, 0.92), rgba(255, 255, 255, 0.98));
		border: 1px solid rgba(32, 59, 53, 0.08);
		display: grid;
		gap: 16px;
	}

	.reservation-summary {
		display: flex;
		justify-content: space-between;
		gap: 16px;
		align-items: start;
	}

	.reservation-summary p,
	.reservation-meta p {
		margin: 4px 0 0;
	}

	.reservation-meta {
		display: grid;
		gap: 6px;
	}

	.notes-field {
		gap: 10px;
	}

	.card-actions {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
	}

	.status-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 8px 12px;
		border-radius: 999px;
		font-weight: 800;
		text-transform: capitalize;
	}

	.status-pill.pending {
		background: rgba(224, 155, 45, 0.18);
		color: #8a5400;
	}

	.status-pill.confirmed {
		background: rgba(46, 110, 95, 0.16);
		color: #2e6e5f;
	}

	.status-pill.completed {
		background: rgba(40, 85, 145, 0.16);
		color: #285591;
	}

	.status-pill.cancelled {
		background: rgba(157, 47, 47, 0.16);
		color: #9d2f2f;
	}

	.message,
	.loading-copy,
	.empty-state {
		margin: 0;
	}

	.message {
		padding: 12px 14px;
		border-radius: 14px;
		font-weight: 700;
	}

	.message.success {
		background: rgba(46, 110, 95, 0.14);
		color: #1f5a4c;
	}

	.message.error {
		background: rgba(157, 47, 47, 0.12);
		color: #8a2727;
	}

	.loading-copy,
	.empty-state {
		color: #45645c;
	}

	button:disabled {
		opacity: 0.6;
		cursor: wait;
	}

	@media (max-width: 720px) {
		.dashboard-shell {
			padding: 18px;
		}

		.panel {
			padding: 24px;
		}

		.panel-header,
		.reservation-summary {
			align-items: start;
			flex-direction: column;
		}
	}
</style>
