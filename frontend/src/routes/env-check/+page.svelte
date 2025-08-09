<!-- src/routes/env-check/+page.svelte -->

<script lang="ts">
	// Import PUBLIC_ environment variables at runtime
	// This doesn't look in your filesystem — SvelteKit injects this module automatically
	import { env } from '$env/dynamic/public';

	// Pull our Supabase variables out of the env object
	const supabaseUrl = env.PUBLIC_SUPABASE_URL;
	const supabaseAnonKey = env.PUBLIC_SUPABASE_ANON_KEY;

	// Check if they look correct
	const urlLooksValid = typeof supabaseUrl === 'string' && supabaseUrl.startsWith('https://');

	const anonKeyLooksPresent = typeof supabaseAnonKey === 'string' && supabaseAnonKey.length > 20;

	// Show only the tail of each value for visual confirmation
	const urlTail = supabaseUrl ? supabaseUrl.slice(-10) : '(none)';
	const anonTail = supabaseAnonKey ? supabaseAnonKey.slice(-6) : '(none)';
</script>

<h1 class="mb-4 text-2xl font-semibold">Supabase Environment Check</h1>

<p class={urlLooksValid ? 'text-green-600' : 'text-red-600'}>
	Supabase URL:
	{#if urlLooksValid}
		looks set ✓ <span class="text-gray-500">(…{urlTail})</span>
	{:else}
		missing or malformed
	{/if}
</p>

<p class={anonKeyLooksPresent ? 'text-green-600' : 'text-red-600'}>
	Supabase anon key:
	{#if anonKeyLooksPresent}
		looks set ✓ <span class="text-gray-500">(…{anonTail})</span>
	{:else}
		missing
	{/if}
</p>

<p class="mt-4 text-sm text-gray-500">You can delete this page after we finish setup.</p>
