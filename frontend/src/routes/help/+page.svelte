<script lang="ts">
	import { HelpCircle } from '@lucide/svelte';
	import { fade } from 'svelte/transition';
</script>

<div class="min-h-screen px-4 py-12 sm:px-6 lg:px-8">
	<div class="mx-auto max-w-4xl">
		<!-- Header -->
		<div class="mb-12 text-center" in:fade={{ duration: 250 }}>
			<div class="mb-6 inline-flex items-center gap-3">
				<div
					class="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/30 bg-white/20 bg-gradient-to-r from-purple-500 to-pink-500 backdrop-blur-sm"
				>
					<HelpCircle class="h-8 w-8 text-white" />
				</div>
			</div>

			<h1 class="mb-4 text-4xl font-bold text-white">Help & About</h1>
			<p class="text-xl text-white/80">Get help or learn more about CodeSense.</p>
		</div>

		<!-- Card -->
		<div
			class="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md"
			in:fade={{ duration: 200 }}
		>
			<div class="rounded-t-2xl border-b border-white/10 px-6 py-4">
				<h2 class="text-lg font-semibold text-white">About CodeSense</h2>
			</div>

			<div class="space-y-4 p-6">
				<p class="text-white/80">
					CodeSense is a tool that bridges the gap between code and business outcomes. It analyzes
					your codebase or project and produces a clear, high level summary of the problem it solves
					and the value it creates.
				</p>
				<p class="text-white/80">
					For support, email <a
						class="underline hover:no-underline"
						href="mailto:support@codesense.app">support@codesense.app</a
					>.
				</p>
			</div>
		</div>
	</div>
</div>
