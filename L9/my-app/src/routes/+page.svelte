<!--
	+page.svelte (root page — acts like the App.svelte root component)
	Demonstrates component composition: importing child components and
	rendering them, including passing data via props.
-->

<script lang="ts">
	import HelloWorld from '$lib/HelloWorld.svelte';
	import Counter from '$lib/Counter.svelte';
	import Profile from '$lib/Profile.svelte';
</script>

<main>
	<Profile
		name="Marcus"
		city="Berlin"
		age={47}
		description="Marcus leads product workshops, cycles across the city on weekends, and keeps a notebook full of interface sketches."
	/>
	<header>
		<h1>Svelte Fundamentals</h1>
		<p>
			A small tour of components, reactivity, events, and props — the building blocks of any modern
			frontend framework.
		</p>
	</header>

	<!-- 1. A simple, static component -->
	<HelloWorld />

	<!-- 2. Reactivity + events: state changes update the UI automatically -->
	<Counter />

	<!-- 3. Props: parent passes dynamic data into the child component -->
	<section class="profiles">
		<h2>Profiles (passed via props)</h2>
		<div class="grid">
			<Profile
				name="Alice"
				city="Paris"
				age={30}
				description="Alice is a pastry chef who documents neighborhood cafes and tests new dessert menus every month."
			/>
			<Profile
				name="Bob"
				city="Tokyo"
				age={18}
				description="Bob studies robotics, spends late evenings building keyboard firmware, and never misses a local arcade tournament."
			/>
			<Profile
				name="Carla"
				city="São Paulo"
				age={27}
				description="Carla works in editorial design, collects vintage magazines, and runs typography meetups for students."
			/>
		</div>
	</section>
</main>

<style>
	main {
		max-width: 720px;
		margin: 2rem auto;
		padding: 0 1rem;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		font-family: system-ui, sans-serif;
		color: #0f172a;
	}

	header h1 {
		margin: 0 0 0.25rem;
		color: #ff3e00;
	}

	header p {
		margin: 0;
		color: #475569;
	}

	.profiles h2 {
		margin: 0 0 0.5rem;
		color: #ff3e00;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 0.75rem;
	}
</style>
