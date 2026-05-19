<script lang="ts">
	import { onMount } from 'svelte';
	import { createReservation, fetchMenuItems, getApiErrorMessage } from '$lib/api';
	import MenuCard from '$lib/components/MenuCard.svelte';
	import type { MenuItem, ReservationCreatePayload, ReservationResponse } from '$lib/types';

	const shopName = 'Bean & Brew';
	const defaultCategory = 'All';
	const maxAdvanceDays = 60;
	const aboutImage =
		'https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=1200&q=80';
	const navigationLinks = [
		{ href: '#hero', label: 'Home' },
		{ href: '#menu', label: 'Menu' },
		{ href: '#about', label: 'About' },
		{ href: '#reservation', label: 'Reserve' },
		{ href: '#contact', label: 'Contact' },
		{ href: '/login', label: 'Staff Login' }
	];
	const footerColumns = [
		{
			title: shopName,
			lines: ['Specialty coffee & pastries since 2018.']
		},
		{
			title: 'Hours',
			lines: ['Mon - Fri: 7 AM - 7 PM', 'Sat - Sun: 8 AM - 5 PM']
		},
		{
			title: 'Location',
			lines: ['42 Maple Street', 'Portland, OR 97201']
		},
		{
			title: 'Connect',
			lines: ['hello@beanandbrew.com', '(503) 555-0172']
		}
	];

	let menuItems = $state<MenuItem[]>([]);
	let displayedMenuItems = $state<MenuItem[]>([]);
	let categories = $state<string[]>([]);
	let activeCategory = $state(defaultCategory);
	let menuStatus = $state('Loading menu...');
	let isDarkTheme = $state(false);

	let contactName = $state('');
	let contactEmail = $state('');
	let reservationDate = $state('');
	let reservationTime = $state('');
	let guestCount = $state<number | undefined>(undefined);
	let specialRequests = $state('');
	let reservationStatus = $state('');
	let reservationStatusType = $state<'success' | 'error' | ''>('');

	const currentYear = new Date().getFullYear();

	function getCategories(items: MenuItem[]): string[] {
		const uniqueCategories = [...new Set(items.map((item) => item.category))];
		return [defaultCategory, ...uniqueCategories];
	}

	function syncThemeClass(): void {
		document.body.classList.toggle('dark-theme', isDarkTheme);
	}

	function toggleTheme(): void {
		isDarkTheme = !isDarkTheme;
		localStorage.setItem('themePreference', isDarkTheme ? 'dark' : 'light');
		syncThemeClass();
	}

	async function loadMenuData(): Promise<void> {
		menuStatus = 'Loading menu...';

		try {
			menuItems = await fetchMenuItems();
			displayedMenuItems = menuItems;
			categories = getCategories(menuItems);
			menuStatus = displayedMenuItems.length === 0 ? 'No items found for this category.' : '';
		} catch (error) {
			console.error(error);
			menuStatus = 'Menu unavailable right now. Please refresh and try again.';
		}
	}

	async function handleCategoryChange(category: string): Promise<void> {
		activeCategory = category;
		menuStatus = 'Loading menu...';
		displayedMenuItems = [];

		try {
			displayedMenuItems =
				category === defaultCategory && menuItems.length > 0
					? menuItems
					: await fetchMenuItems(category);
			menuStatus = displayedMenuItems.length === 0 ? 'No items found for this category.' : '';
		} catch (error) {
			console.error(error);
			menuStatus = 'Menu unavailable right now. Please refresh and try again.';
		}
	}

	function showReservationMessage(message: string, type: 'success' | 'error'): void {
		reservationStatus = message;
		reservationStatusType = type;
	}

	function validateReservation(): string {
		const parsedGuestCount = Number(guestCount);
		const reservationDateTime = new Date(`${reservationDate}T${reservationTime}`);

		if (!Number.isInteger(parsedGuestCount) || parsedGuestCount < 1 || parsedGuestCount > 20) {
			return 'Guests must be a whole number between 1 and 20.';
		}

		if (Number.isNaN(reservationDateTime.getTime())) {
			return 'Please choose a valid reservation date and time.';
		}

		const now = new Date();
		if (reservationDateTime < now) {
			return 'Reservation date/time must be in the future.';
		}

		const maxDate = new Date();
		maxDate.setDate(maxDate.getDate() + maxAdvanceDays);
		if (reservationDateTime > maxDate) {
			return `Reservations can only be made up to ${maxAdvanceDays} days in advance.`;
		}

		return '';
	}

	function resetReservationForm(): void {
		contactName = '';
		contactEmail = '';
		reservationDate = '';
		reservationTime = '';
		guestCount = undefined;
		specialRequests = '';
	}

	async function handleReservationSubmit(event: SubmitEvent): Promise<void> {
		event.preventDefault();

		const validationError = validateReservation();
		if (validationError) {
			showReservationMessage(validationError, 'error');
			return;
		}

		const trimmedName = contactName.trim();
		const parsedGuestCount = Number(guestCount);
		const reservationPayload: ReservationCreatePayload = {
			contact_name: trimmedName,
			contact_email: contactEmail.trim(),
			date: reservationDate,
			time: reservationTime,
			guest_count: parsedGuestCount,
			special_requests: specialRequests.trim() || null
		};

		try {
			const savedReservation: ReservationResponse = await createReservation(reservationPayload);
			showReservationMessage(
				`Thanks, ${trimmedName}! Reservation #${savedReservation.id} for ${parsedGuestCount} guests at ${shopName} is confirmed for ${reservationDate} at ${reservationTime}.`,
				'success'
			);
			resetReservationForm();
		} catch (error) {
			console.error(error);
			showReservationMessage(
				getApiErrorMessage(
					error,
					'Unable to reach the reservation service right now. Please try again.'
				),
				'error'
			);
		}
	}

	onMount(() => {
		const savedTheme = localStorage.getItem('themePreference');
		isDarkTheme = savedTheme === 'dark';
		syncThemeClass();
		void loadMenuData();

		return () => {
			document.body.classList.remove('dark-theme');
		};
	});
</script>

<svelte:head>
	<title>{shopName} - Coffee Shop</title>
</svelte:head>

<nav class="navbar">
	<div class="nav-container">
		<a href="#hero" class="logo">{shopName}</a>
		<ul class="nav-links">
			{#each navigationLinks as link (link.href)}
				<li><a href={link.href}>{link.label}</a></li>
			{/each}
		</ul>
		<button class="theme-toggle" type="button" onclick={toggleTheme}>Toggle Theme</button>
	</div>
</nav>

<section id="hero" class="hero">
	<div class="hero-overlay">
		<h1>Crafted with Passion,<br />Served with Love</h1>
		<p>Specialty coffee &amp; fresh pastries in the heart of Portland</p>
		<a href="#menu" class="btn">View Our Menu</a>
	</div>
</section>

<section id="menu" class="section">
	<h2 class="section-title">Our Menu</h2>
	<p class="section-subtitle">Handcrafted drinks &amp; baked-fresh-daily treats</p>

	{#if categories.length > 0}
		<div class="menu-controls">
			{#each categories as category (category)}
				<button
					type="button"
					class="filter-btn"
					class:active={category === activeCategory}
					onclick={() => void handleCategoryChange(category)}
				>
					{category}
				</button>
			{/each}
		</div>
	{/if}

	<div class="menu-grid" aria-live="polite">
		{#if menuStatus}
			<p class="menu-status">{menuStatus}</p>
		{:else}
			{#each displayedMenuItems as item (item.id)}
				<MenuCard {item} />
			{/each}
		{/if}
	</div>
</section>

<section id="about" class="section about">
	<div class="about-container">
		<div class="about-image">
			<img src={aboutImage} alt="Barista carefully pouring espresso at the coffee bar" />
		</div>
		<div class="about-text">
			<h2>Our Story</h2>
			<p>
				Bean &amp; Brew started as a tiny cart on SW 3rd Avenue back in 2018. What began with a
				single espresso machine and a dream has grown into Portland's favorite neighborhood coffee
				house.
			</p>
			<p>
				We source our beans directly from family farms in Colombia, Ethiopia, and Guatemala, then
				roast them in small batches at our in-house roastery. Every cup tells a story - from seed to
				sip.
			</p>
			<p>
				Our pastries are baked fresh each morning by our in-house baker using local, organic
				ingredients. We believe great food and great coffee deserve each other.
			</p>
		</div>
	</div>
</section>

<section id="reservation" class="section reservation">
	<h2 class="section-title">Reserve a Table</h2>
	<p class="section-subtitle">Book ahead for groups of 4 or more</p>

	<form class="reservation-form" onsubmit={handleReservationSubmit}>
		<div class="form-row">
			<div class="form-group">
				<label for="name">Full Name</label>
				<input id="name" type="text" placeholder="Jane Doe" bind:value={contactName} required />
			</div>
			<div class="form-group">
				<label for="email">Email</label>
				<input
					id="email"
					type="email"
					placeholder="jane@email.com"
					bind:value={contactEmail}
					required
				/>
			</div>
		</div>
		<div class="form-row">
			<div class="form-group">
				<label for="date">Date</label>
				<input id="date" type="date" bind:value={reservationDate} required />
			</div>
			<div class="form-group">
				<label for="time">Time</label>
				<input id="time" type="time" bind:value={reservationTime} required />
			</div>
			<div class="form-group">
				<label for="guests">Guests</label>
				<input
					id="guests"
					type="number"
					min="1"
					max="20"
					placeholder="4"
					bind:value={guestCount}
					required
				/>
			</div>
		</div>
		<div class="form-group">
			<label for="notes">Special Requests</label>
			<textarea
				id="notes"
				rows="3"
				placeholder="Allergies, celebrations, seating preference..."
				bind:value={specialRequests}
			></textarea>
		</div>
		<button type="submit" class="btn">Book Now</button>
		<p
			class="form-status"
			class:success={reservationStatusType === 'success'}
			class:error={reservationStatusType === 'error'}
			aria-live="polite"
		>
			{reservationStatus}
		</p>
	</form>
</section>

<footer id="contact" class="footer">
	<div class="footer-container">
		{#each footerColumns as column (column.title)}
			<div class="footer-col">
				<h3>{column.title}</h3>
				{#each column.lines as line (line)}
					<p>{line}</p>
				{/each}
			</div>
		{/each}
	</div>
	<div class="footer-bottom">
		<p>&copy; {currentYear} {shopName}. All rights reserved.</p>
	</div>
</footer>

<style>
	:global(html) {
		scroll-behavior: smooth;
	}

	:global(body) {
		--primary: #4e342e;
		--primary-light: #6d4c41;
		--accent: #ff8f00;
		--accent-light: #ffcc80;
		--bg: #fffaf5;
		--bg-alt: #efebe9;
		--text: #3e2723;
		--text-light: #795548;
		--white: #fff;
		--radius: 10px;
		--shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		--transition: 0.3s ease;
		margin: 0;
		font-family: 'Nunito', sans-serif;
		color: var(--text);
		background-color: var(--bg);
		line-height: 1.7;
		transition:
			background-color var(--transition),
			color var(--transition);
	}

	:global(body.dark-theme) {
		--primary: #cebfb8;
		--primary-light: #eaded8;
		--accent: #f8b458;
		--accent-light: #f7d8ac;
		--bg: #1f1a18;
		--bg-alt: #2b2421;
		--text: #f5e8e1;
		--text-light: #dcc6bb;
		--white: #2f2724;
		--shadow: 0 8px 22px rgba(0, 0, 0, 0.4);
	}

	* {
		box-sizing: border-box;
	}

	img {
		display: block;
		max-width: 100%;
	}

	a {
		text-decoration: none;
		color: inherit;
	}

	.section {
		padding: 80px 24px;
		max-width: 1100px;
		margin: 0 auto;
	}

	.section-title {
		font-family: 'Playfair Display', serif;
		font-size: 2.2rem;
		text-align: center;
		color: var(--primary);
		margin-bottom: 8px;
	}

	.section-title::after {
		content: '';
		display: block;
		width: 60px;
		height: 3px;
		background: var(--accent);
		margin: 12px auto 0;
		border-radius: 2px;
	}

	.section-subtitle {
		text-align: center;
		color: var(--text-light);
		margin-bottom: 40px;
	}

	.btn {
		display: inline-block;
		background-color: var(--accent);
		color: var(--white);
		padding: 12px 32px;
		border-radius: var(--radius);
		font-size: 1rem;
		font-weight: 700;
		border: none;
		cursor: pointer;
		transition:
			background-color var(--transition),
			transform var(--transition);
	}

	.btn:hover {
		background-color: #e65100;
		transform: translateY(-2px);
	}

	.navbar {
		position: sticky;
		top: 0;
		z-index: 100;
		background-color: var(--primary);
	}

	.nav-container {
		max-width: 1100px;
		margin: 0 auto;
		padding: 16px 24px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.logo {
		font-family: 'Playfair Display', serif;
		font-size: 1.5rem;
		color: var(--white);
	}

	.nav-links {
		list-style: none;
		display: flex;
		gap: 28px;
		padding: 0;
		margin: 0;
	}

	.nav-links a {
		color: var(--accent-light);
		font-weight: 600;
		transition: color var(--transition);
	}

	.nav-links a:hover {
		color: var(--white);
	}

	.theme-toggle {
		background: transparent;
		color: var(--accent-light);
		border: 1px solid var(--accent-light);
		border-radius: 999px;
		padding: 6px 14px;
		font-size: 0.9rem;
		font-weight: 700;
		cursor: pointer;
		transition:
			color var(--transition),
			border-color var(--transition),
			background-color var(--transition);
	}

	.theme-toggle:hover {
		color: var(--white);
		border-color: var(--white);
		background-color: rgba(255, 255, 255, 0.12);
	}

	.hero {
		background:
			linear-gradient(rgba(62, 39, 35, 0.6), rgba(62, 39, 35, 0.6)),
			url('https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1600&q=80')
				center / cover no-repeat;
		padding: 0;
		max-width: none;
	}

	.hero-overlay {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		min-height: 70vh;
		padding: 40px 24px;
		color: var(--white);
	}

	.hero h1 {
		font-family: 'Playfair Display', serif;
		font-size: 3rem;
		line-height: 1.2;
		margin-bottom: 16px;
	}

	.hero p {
		font-size: 1.2rem;
		color: var(--accent-light);
		margin-bottom: 28px;
	}

	.menu-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 28px;
	}

	.menu-controls {
		display: flex;
		justify-content: center;
		flex-wrap: wrap;
		gap: 10px;
		margin-bottom: 24px;
	}

	.filter-btn {
		border: 1px solid var(--primary);
		color: var(--primary);
		background: transparent;
		padding: 8px 16px;
		border-radius: 999px;
		font-weight: 700;
		cursor: pointer;
		transition:
			background-color var(--transition),
			color var(--transition),
			transform var(--transition);
	}

	.filter-btn:hover {
		transform: translateY(-1px);
	}

	.filter-btn.active {
		background-color: var(--primary);
		color: var(--bg);
	}

	.menu-status {
		text-align: center;
		color: var(--text-light);
		grid-column: 1 / -1;
	}

	.about-container {
		display: flex;
		gap: 40px;
		align-items: center;
	}

	.about-image {
		flex: 1;
		min-width: 0;
	}

	.about-image img {
		border-radius: var(--radius);
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.about-text {
		flex: 1;
	}

	.about-text h2 {
		font-family: 'Playfair Display', serif;
		font-size: 2rem;
		color: var(--primary);
		margin-bottom: 16px;
	}

	.about-text p {
		margin-bottom: 14px;
		color: var(--text-light);
	}

	.reservation {
		background-color: var(--bg-alt);
		max-width: none;
		padding: 80px 24px;
	}

	.reservation-form {
		max-width: 700px;
		margin: 0 auto;
	}

	.form-row {
		display: flex;
		gap: 16px;
		margin-bottom: 16px;
	}

	.form-group {
		flex: 1;
		display: flex;
		flex-direction: column;
		margin-bottom: 16px;
	}

	.form-group label {
		font-weight: 700;
		font-size: 0.9rem;
		margin-bottom: 4px;
		color: var(--primary);
	}

	.form-group input,
	.form-group textarea {
		padding: 10px 14px;
		border: 2px solid #d7ccc8;
		border-radius: var(--radius);
		font-family: inherit;
		font-size: 1rem;
		transition:
			border-color var(--transition),
			box-shadow var(--transition);
	}

	.form-group input:focus,
	.form-group textarea:focus {
		outline: none;
		border-color: var(--accent);
		box-shadow: 0 0 0 3px rgba(255, 143, 0, 0.2);
	}

	.reservation-form .btn {
		width: 100%;
		padding: 14px;
		font-size: 1.05rem;
	}

	.form-status {
		margin-top: 14px;
		font-size: 0.95rem;
		min-height: 22px;
	}

	.form-status.success {
		color: #2e7d32;
	}

	.form-status.error {
		color: #c62828;
	}

	:global(body.dark-theme) .form-status.success {
		color: #8dda92;
	}

	:global(body.dark-theme) .form-status.error {
		color: #ff8a80;
	}

	.footer {
		background-color: var(--primary);
		color: var(--accent-light);
		padding: 48px 24px 24px;
	}

	.footer-container {
		max-width: 1100px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		gap: 24px;
		flex-wrap: wrap;
	}

	.footer-col h3 {
		color: var(--white);
		font-size: 1.1rem;
		margin-bottom: 8px;
	}

	.footer-col p {
		font-size: 0.95rem;
		margin-bottom: 4px;
	}

	.footer-bottom {
		text-align: center;
		margin-top: 36px;
		padding-top: 20px;
		border-top: 1px solid rgba(255, 255, 255, 0.15);
		font-size: 0.85rem;
	}

	@media (max-width: 768px) {
		.nav-container {
			flex-direction: column;
			gap: 12px;
		}

		.nav-links {
			gap: 16px;
			flex-wrap: wrap;
			justify-content: center;
		}

		.hero h1 {
			font-size: 2rem;
		}

		.about-container {
			flex-direction: column;
		}

		.form-row {
			flex-direction: column;
			gap: 0;
		}

		.footer-container {
			flex-direction: column;
			text-align: center;
		}
	}
</style>
