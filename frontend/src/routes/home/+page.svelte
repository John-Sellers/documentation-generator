<script lang="ts">
	import { Github, FolderOpen, Upload, Code, ArrowRight } from '@lucide/svelte';
	import { fade } from 'svelte/transition';

	type Feature = {
		icon: typeof Github;
		title: string;
		description: string;
		color: string;
	};

	const features: Feature[] = [
		{
			icon: Github,
			title: 'GitHub Repositories',
			description: 'Analyze entire public or private repositories directly from their URL.',
			color: 'from-indigo-500 to-purple-600'
		},
		{
			icon: FolderOpen,
			title: 'Specific Directories',
			description: 'Focus on a single folder within a repository to narrow the scope.',
			color: 'from-sky-500 to-indigo-500'
		},
		{
			icon: Upload,
			title: 'ZIP Files',
			description: 'Upload your project as a compressed ZIP file for a complete analysis.',
			color: 'from-cyan-500 to-sky-500'
		},
		{
			icon: Code,
			title: 'Code Snippets',
			description: 'Quickly paste a snippet of code to understand its business context.',
			color: 'from-teal-500 to-cyan-500'
		}
	];
</script>

<div class="px-4 py-12 sm:px-6 lg:px-8">
	<div class="mx-auto max-w-5xl">
		<!-- Hero -->
		<div in:fade={{ duration: 400 }} class="mb-16 text-center">
			<h1 class="mb-6 text-5xl font-extrabold leading-tight text-white md:text-6xl">
				Unlock the Business Value
				<span
					class="mt-2 block bg-gradient-to-r from-sky-300 to-indigo-400 bg-clip-text text-transparent"
				>
					Hidden in Your Code
				</span>
			</h1>

			<p class="mx-auto mb-8 max-w-3xl text-xl text-white/80">
				CodeSense automatically generates clear, non technical summaries that explain the business
				purpose and value of any code, project, or repository.
			</p>

			<a
				href="/submit"
				class="group inline-flex items-center rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 px-8 py-4 text-lg font-bold text-white transition-transform hover:from-sky-600 hover:to-indigo-600"
			>
				Start Analyzing Now
				<ArrowRight class="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
			</a>
		</div>

		<!-- Features -->
		<div class="mb-16">
			<h2 class="mb-8 text-center text-3xl font-bold text-white">Supported Inputs</h2>

			<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
				{#each features as feature, i}
					<div
						in:fade={{ duration: 300, delay: 100 * i }}
						class="h-full rounded-2xl border border-white/10 bg-black/20 text-center backdrop-blur-md transition-all duration-300 hover:bg-black/30"
					>
						<div class="p-6">
							<div
								class={'mx-auto mb-4 h-16 w-16 bg-gradient-to-r ' +
									feature.color +
									' flex items-center justify-center rounded-2xl'}
							>
								<svelte:component this={feature.icon} class="h-8 w-8 text-white" />
							</div>

							<h3 class="mb-2 text-lg font-semibold text-white">{feature.title}</h3>
							<p class="text-sm text-white/70">{feature.description}</p>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>
