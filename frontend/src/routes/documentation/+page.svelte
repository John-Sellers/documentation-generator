<script lang="ts">
	// Icons come from the maintained package
	import { BookOpen } from '@lucide/svelte';
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
					<BookOpen class="h-8 w-8 text-white" />
				</div>
			</div>

			<h1 class="mb-4 text-4xl font-bold text-white">Documentation</h1>
			<p class="text-xl text-white/80">How to use CodeSense to its full potential.</p>
		</div>

		<!-- Card -->
		<div
			class="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md"
			in:fade={{ duration: 200 }}
		>
			<div class="rounded-t-2xl border-b border-white/10 px-6 py-4">
				<h2 class="text-lg font-semibold text-white">Coming Soon</h2>
			</div>

			<div class="p-6">
				<p class="text-white/80">
					Our team is hard at work creating comprehensive documentation. Please check back soon for
					detailed guides and tutorials on how to integrate and use CodeSense effectively.
				</p>
			</div>
		</div>
	</div>
</div>
