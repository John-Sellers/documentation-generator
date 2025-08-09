<script>
	let open = false;
	function toggle() {
		open = !open;
	}
</script>

<div class="relative">
	<button class="rounded bg-white/10 px-3 py-2 hover:bg-white/20" on:click={toggle}> User </button>

	{#if open}
		<div
			class="absolute right-0 mt-2 w-40 rounded border border-white/10 bg-black/80 p-2 backdrop-blur"
		>
			<a href="/Profile" class="block rounded px-3 py-2 hover:bg-white/10">Profile</a>
			<a href="/Logout" class="block rounded px-3 py-2 hover:bg-white/10">Logout</a>
		</div>
	{/if}
</div>
