<script>
	const tabs = [
		{ name: 'Submit', href: '/submit' },
		{ name: 'History', href: '/history' }
	];
</script>

<nav class="z-10 border-b border-white/10 bg-black/20">
	<div class="mx-auto flex h-12 max-w-7xl items-center gap-2 px-4 sm:px-6 lg:px-8">
		{#each tabs as t}
			<a href={t.href} class="rounded-full bg-white/5 px-3 py-1.5 text-sm hover:bg-white/15">
				{t.name}
			</a>
		{/each}
	</div>
</nav>
