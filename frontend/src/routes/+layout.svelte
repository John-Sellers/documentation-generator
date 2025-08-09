<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import '../app.css';

	// Icons for the top navigation
	import { Code2, FileText, Home as HomeIcon, BookOpen, HelpCircle } from '@lucide/svelte';

	// Your tiny building blocks from Step 1
	import UserMenu from '$lib/components/UserMenu.svelte';
	import SubNav from '$lib/components/SubNav.svelte';
	import { User } from '$lib/api/User';

	// Simple state
	let user: { id: number; name: string } | null = null;
	let isLoading = true;

	// Check who is logged in
	async function checkUser() {
		try {
			user = await User.me();
		} catch {
			user = null;
		} finally {
			isLoading = false;
		}
	}

	// Run once when the page loads
	onMount(checkUser);

	// Recompute on route change
	$: pathname = $page.url.pathname;
	$: isWorkspacePage = pathname === '/submit' || pathname === '/history';
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
				<a href="/home" class="group flex items-center gap-3">
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

				<!-- Links and user menu -->
				<div class="hidden items-center gap-4 md:flex">
					<div class="flex items-center gap-2">
						<a href="/home">
							<div
								class={'flex items-center gap-2 rounded-full border border-transparent bg-white/5 px-4 py-2 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white ' +
									($page.url.pathname === '/home' ? 'border-white/20 bg-white/20 text-white' : '')}
							>
								<HomeIcon class="h-4 w-4" />
								<span class="text-sm font-medium">Home</span>
							</div>
						</a>

						<a href="/documentation">
							<div
								class={'flex items-center gap-2 rounded-full border border-transparent bg-white/5 px-4 py-2 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white ' +
									($page.url.pathname === '/documentation'
										? 'border-white/20 bg-white/20 text-white'
										: '')}
							>
								<BookOpen class="h-4 w-4" />
								<span class="text-sm font-medium">Documentation</span>
							</div>
						</a>

						<a href="/help">
							<div
								class={'flex items-center gap-2 rounded-full border border-transparent bg-white/5 px-4 py-2 text-white/80 backdrop-blur-sm transition-colors hover:bg-white/20 hover:text-white ' +
									($page.url.pathname === '/help' ? 'border-white/20 bg-white/20 text-white' : '')}
							>
								<HelpCircle class="h-4 w-4" />
								<span class="text-sm font-medium">Help</span>
							</div>
						</a>
					</div>

					<UserMenu />
				</div>

				<!-- Mobile user menu -->
				<div class="md:hidden">
					<UserMenu />
				</div>
			</div>
		</div>
	</nav>

	<!-- Sub navigation only for workspace pages and only if logged in -->
	{#if !isLoading && user && isWorkspacePage}
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
