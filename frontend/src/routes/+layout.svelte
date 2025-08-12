<script lang="ts">
	// Core SvelteKit helpers
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { invalidate, goto } from '$app/navigation';

	// Project styles
	import '../app.css';

	// Lucide icons as direct component imports
	import Code2 from '@lucide/svelte/icons/code-2';
	import FileText from '@lucide/svelte/icons/file-text';
	import HomeIcon from '@lucide/svelte/icons/home';
	import BookOpen from '@lucide/svelte/icons/book-open';
	import HelpCircle from '@lucide/svelte/icons/help-circle';

	// Your sub navigation
	import SubNav from '../lib/components/SubNav.svelte';

	// Types
	import type { Session } from '@supabase/supabase-js';

	// Data from +layout.server.ts and +layout.ts
	// supabase is the browser client and session is null when logged out
	export let data: { supabase: any; session: Session | null };

	// Keep locals in sync if data changes
	let { supabase, session } = data;
	$: ({ supabase, session } = data);

	// Convenience values from the $page store
	$: pathname = $page.url.pathname;

	onMount(() => {
		const {
			data: { subscription }
		} = supabase.auth.onAuthStateChange((_event: string, newSession: Session) => {
			// Compare the "expires_at" we’re currently rendering with what Supabase just told us
			const oldExp = data.session?.expires_at ?? null;
			const newExp = newSession?.expires_at ?? null;

			if (oldExp !== newExp) {
				// Triggers +layout.ts to re-run and return the fresh session
				invalidate('supabase:auth');
			}
		});

		return () => subscription.unsubscribe();
	});

	// Simple logout that clears the session and moves to Login
	async function handleLogout() {
		try {
			await supabase.auth.signOut();
			await goto('/login');
			// The listener above will refresh session data and the UI will update
		} catch (e) {
			console.error('Logout failed', e);
		}
	}
</script>

<!-- Pretty gradient background -->
<div
	class="relative flex min-h-screen flex-col overflow-hidden bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white"
>
	<!-- Soft floating blobs -->
	<div class="pointer-events-none absolute inset-0 overflow-hidden">
		<div
			class="absolute left-1/4 top-1/4 h-96 w-96 animate-pulse rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-600/20 blur-3xl"
		></div>
		<div
			class="absolute bottom-1/4 right-1/4 h-80 w-80 animate-pulse rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-600/20 blur-3xl"
		></div>
		<div
			class="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-gradient-to-r from-sky-400/20 to-indigo-500/20 blur-3xl"
		></div>
	</div>

	<!-- Top navigation bar -->
	<nav class="relative z-10 border-b border-white/10 bg-black/30 backdrop-blur-md">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="flex h-16 items-center justify-between">
				<!-- App logo and name -->
				<a href="/" class="group flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-xl border border-white/30 bg-white/20 bg-gradient-to-r from-sky-500 to-indigo-500 backdrop-blur-sm transition-transform group-hover:scale-105"
					>
						<Code2 class="h-5 w-5 text-white" />
					</div>
					<div class="text-white">
						<h1 class="text-xl font-bold">CodeSense</h1>
						<p class="text-xs text-white/80">Business Intelligence</p>
					</div>
				</a>

				<!-- Links and auth actions -->
				<div class="hidden items-center gap-4 md:flex">
					<div class="flex items-center gap-2">
						<a href="/">
							<div
								class={'flex items-center gap-2 rounded-full border border-transparent bg-white/5 px-4 py-2 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white ' +
									(pathname === '/' ? 'border-white/20 bg-white/20 text-white' : '')}
							>
								<HomeIcon class="h-4 w-4" />
								<span class="text-sm font-medium">Home</span>
							</div>
						</a>

						<a href="/documentation">
							<div
								class={'flex items-center gap-2 rounded-full border border-transparent bg-white/5 px-4 py-2 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white ' +
									(pathname === '/documentation' ? 'border-white/20 bg-white/20 text-white' : '')}
							>
								<BookOpen class="h-4 w-4" />
								<span class="text-sm font-medium">Documentation</span>
							</div>
						</a>

						<a href="/help">
							<div
								class={'flex items-center gap-2 rounded-full border border-transparent bg-white/5 px-4 py-2 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white ' +
									(pathname === '/help' ? 'border-white/20 bg-white/20 text-white' : '')}
							>
								<HelpCircle class="h-4 w-4" />
								<span class="text-sm font-medium">Help</span>
							</div>
						</a>
					</div>

					<!-- Right side auth action. Login when logged out. Logout when logged in. -->
					{#if data.session}
						<button
							class="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm text-white/90 hover:bg-white/20"
							on:click={handleLogout}
						>
							Logout
						</button>
					{:else}
						<a
							href="/login"
							class="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm text-white/90 hover:bg-white/20"
						>
							Login/Signup
						</a>
					{/if}
				</div>

				<!-- Mobile auth action -->
				<div class="md:hidden">
					{#if data.session}
						<button
							class="rounded border border-white/20 bg-white/10 px-3 py-1 text-sm text-white/90"
							on:click={handleLogout}
						>
							Logout
						</button>
					{:else}
						<a
							href="/login"
							class="rounded border border-white/20 bg-white/10 px-3 py-1 text-sm text-white/90"
						>
							Login
						</a>
					{/if}
				</div>
			</div>
		</div>
	</nav>

	<!-- Sub navigation. Show on every page when signed in. -->
	{#if data.session}
		<SubNav />
	{/if}

	<!-- Main content -->
	<main class="relative z-10 flex-1">
		<slot />
	</main>

	<!-- Footer note -->
	<footer class="relative z-10 border-t border-white/10 bg-black/20 backdrop-blur-md">
		<div class="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-center">
				<div class="flex items-center gap-2 text-sm text-white/60">
					<FileText class="h-4 w-4" />
					<span
						>Your input data is securely processed and not retained beyond generating the
						documentation.</span
					>
				</div>
			</div>
		</div>
	</footer>
</div>
