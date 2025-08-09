<script lang="ts">
	import { Clock, FileText, Github, FolderOpen, Upload, Code, ExternalLink } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';

	// Simple auth flag (replace with your real check later)
	let isAuthed = true;

	// Types + state
	type InputType = 'github_repo' | 'github_repo_directory' | 'zipped_folder' | 'pasted_code';
	type Status = 'completed' | 'failed' | 'processing';
	type SubmissionItem = {
		id: number;
		input_type: InputType;
		input_content: string;
		status: Status;
		created_date: string; // ISO
		summary?: string;
		error_message?: string;
	};

	let submissions: SubmissionItem[] = [];
	let isLoading = true;
	let selectedSubmission: SubmissionItem | null = null;

	// Fake API — swap with your real Submission.list
	async function listSubmissions(_order: string, limit: number): Promise<SubmissionItem[]> {
		await new Promise((r) => setTimeout(r, 400));
		const now = Date.now();
		const demo: SubmissionItem[] = [
			{
				id: now - 1,
				input_type: 'github_repo',
				input_content: 'https://github.com/sveltejs/kit',
				status: 'completed',
				created_date: new Date(now - 30 * 60 * 1000).toISOString(),
				summary: 'SvelteKit app framework with file-based routing.'
			},
			{
				id: now - 2,
				input_type: 'github_repo_directory',
				input_content: 'https://github.com/vercel/next.js/tree/canary/packages/next/src',
				status: 'processing',
				created_date: new Date(now - 90 * 60 * 1000).toISOString()
			}
		];
		return demo.slice(0, limit);
	}

	onMount(async () => {
		try {
			submissions = await listSubmissions('-created_date', 50);
		} finally {
			isLoading = false;
		}
	});

	// Helpers
	function getMethodIcon(t: InputType) {
		switch (t) {
			case 'github_repo':
				return Github;
			case 'github_repo_directory':
				return FolderOpen;
			case 'zipped_folder':
				return Upload;
			case 'pasted_code':
				return Code;
			default:
				return FileText;
		}
	}
	function getMethodColor(t: InputType) {
		switch (t) {
			case 'github_repo':
				return 'from-purple-500 to-blue-500';
			case 'github_repo_directory':
				return 'from-blue-500 to-cyan-500';
			case 'zipped_folder':
				return 'from-cyan-500 to-teal-500';
			case 'pasted_code':
				return 'from-teal-500 to-green-500';
			default:
				return 'from-gray-500 to-gray-600';
		}
	}
	function formatInputType(t: InputType) {
		switch (t) {
			case 'github_repo':
				return 'GitHub Repository';
			case 'github_repo_directory':
				return 'GitHub Directory';
			case 'zipped_folder':
				return 'Uploaded File';
			case 'pasted_code':
				return 'Code Snippet';
		}
	}
	function fmt(iso: string) {
		const d = new Date(iso);
		return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(d);
	}
</script>

{#if !isAuthed}
	<!-- Unauthed view -->
	<div class="flex min-h-screen items-center justify-center p-6">
		<div class="rounded-2xl border border-white/20 bg-white/10 p-6 text-center text-white">
			<p class="mb-4">You must be signed in to view history</p>
			<a href="/home" class="rounded bg-white/20 px-4 py-2 hover:bg-white/30">Go Home</a>
		</div>
	</div>
{:else}
	<!-- Authed view -->
	<div class="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
		<div class="mx-auto max-w-6xl">
			<!-- Header -->
			<div class="mb-12 text-center" in:fade={{ duration: 200 }}>
				<div class="mb-6 inline-flex items-center gap-3">
					<div
						class="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/30 bg-white/20 bg-gradient-to-r from-purple-500 to-pink-500 backdrop-blur-sm"
					>
						<Clock class="h-8 w-8 text-white" />
					</div>
				</div>
				<h1 class="mb-4 text-4xl font-bold text-white">Analysis History</h1>
				<p class="mx-auto max-w-2xl text-xl text-white/80">
					View and manage your previous code analysis results
				</p>
			</div>

			{#if isLoading}
				<!-- Skeletons -->
				<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
					{#each Array(6) as _, i}
						<div
							class="animate-pulse rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md"
							in:fade={{ duration: 150, delay: i * 60 }}
						>
							<div class="p-6">
								<div class="mb-2 h-4 rounded bg-white/20"></div>
								<div class="mb-4 h-3 w-2/3 rounded bg-white/10"></div>
								<div class="mb-2 h-2 w-full rounded bg-white/10"></div>
								<div class="h-2 w-3/4 rounded bg-white/10"></div>
							</div>
						</div>
					{/each}
				</div>
			{:else if submissions.length === 0}
				<!-- Empty state -->
				<div class="py-12 text-center" in:fade>
					<div
						class="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-white/10"
					>
						<FileText class="h-12 w-12 text-white/60" />
					</div>
					<h3 class="mb-2 text-2xl font-semibold text-white">No submissions yet</h3>
					<p class="mb-6 text-white/60">Start by submitting your first code analysis</p>
					<a
						href="/submit"
						class="inline-flex items-center gap-2 rounded bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 text-white hover:from-purple-600 hover:to-pink-600"
					>
						Submit Code Now
					</a>
				</div>
			{:else}
				<!-- Submissions grid -->
				<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
					{#each submissions as s, index (s.id)}
						<button
							type="button"
							class="space-y-3 rounded-2xl border border-white/20 bg-white/10 p-5 text-left backdrop-blur-md transition hover:bg-white/15"
							on:click={() => (selectedSubmission = s)}
							in:fade={{ duration: 150, delay: index * 50 }}
						>
							<div class="flex items-center gap-3">
								<div
									class={'h-12 w-12 bg-gradient-to-r ' +
										getMethodColor(s.input_type) +
										' flex items-center justify-center rounded-xl'}
								>
									<svelte:component this={getMethodIcon(s.input_type)} class="h-6 w-6 text-white" />
								</div>
								<div>
									<div class="font-semibold text-white">{formatInputType(s.input_type)}</div>
									<div class="text-sm text-white/60">{fmt(s.created_date)}</div>
								</div>
							</div>

							<div class="mt-2 line-clamp-3 break-all text-sm text-white/80">
								{s.input_content}
							</div>

							<div class="mt-2">
								{#if s.status === 'completed'}
									<span
										class="inline-block rounded border border-green-400/30 bg-green-500/20 px-2 py-1 text-xs text-green-200"
										>completed</span
									>
								{:else if s.status === 'failed'}
									<span
										class="inline-block rounded border border-red-400/30 bg-red-500/20 px-2 py-1 text-xs text-red-200"
										>failed</span
									>
								{:else}
									<span
										class="inline-block rounded border border-yellow-400/30 bg-yellow-500/20 px-2 py-1 text-xs text-yellow-200"
										>processing</span
									>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			{/if}

			<!-- Modal -->
			{#if selectedSubmission}
				<div
					class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
					role="button"
					aria-label="Close details"
					tabindex="0"
					on:click={() => (selectedSubmission = null)}
					on:keydown={(e) => {
						if (e.key === 'Enter' || e.key === ' ') {
							e.preventDefault();
							selectedSubmission = null;
						}
						if (e.key === 'Escape') {
							selectedSubmission = null;
						}
					}}
					in:fade={{ duration: 120 }}
					out:fade={{ duration: 120 }}
				>
					<!-- Dialog panel -->
					<div
						class="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-2xl border border-white/20 bg-white/10 outline-none backdrop-blur-md"
						role="dialog"
						aria-modal="true"
						aria-labelledby="analysis-dialog-title"
						aria-describedby="analysis-dialog-desc"
						tabindex="-1"
						on:click|stopPropagation
						in:scale={{ duration: 120, start: 0.95 }}
						out:scale={{ duration: 120, start: 0.95 }}
					>
						<div
							class="flex items-center justify-between rounded-t-2xl border-b border-white/10 px-6 py-4"
						>
							<h2 id="analysis-dialog-title" class="text-xl font-semibold text-white">
								Analysis Details
							</h2>
							<button
								type="button"
								class="rounded px-2 py-1 text-white/80 hover:bg-white/10 hover:text-white"
								aria-label="Close"
								on:click={() => (selectedSubmission = null)}
							>
								✕
							</button>
						</div>

						<div id="analysis-dialog-desc" class="space-y-6 p-6 text-white">
							<div class="grid grid-cols-2 gap-4">
								<div>
									<label class="text-sm text-white/60">Method</label>
									<p class="font-medium">{formatInputType(selectedSubmission.input_type)}</p>
								</div>
								<div>
									<label class="text-sm text-white/60">Status</label>
									<p class="capitalize">{selectedSubmission.status}</p>
								</div>
							</div>

							<div>
								<label class="text-sm text-white/60">Input Content</label>
								<div class="mt-2 rounded-lg border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
									<p class="break-all font-mono text-sm text-white/80">
										{selectedSubmission.input_content.length > 200
											? `${selectedSubmission.input_content.substring(0, 200)}...`
											: selectedSubmission.input_content}
									</p>
								</div>
							</div>

							{#if selectedSubmission.summary}
								<div>
									<label class="text-sm text-white/60">Business Summary</label>
									<div
										class="mt-2 rounded-lg border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
									>
										<p class="leading-relaxed">{selectedSubmission.summary}</p>
									</div>
								</div>
							{/if}

							{#if selectedSubmission.error_message}
								<div>
									<label class="text-sm text-red-400">Error Message</label>
									<div
										class="mt-2 rounded-lg border border-red-300/20 bg-red-500/10 p-4 backdrop-blur-sm"
									>
										<p class="text-red-300">{selectedSubmission.error_message}</p>
									</div>
								</div>
							{/if}

							<div class="grid grid-cols-2 gap-4">
								<div>
									<label class="text-sm text-white/60">Submitted</label>
									<p class="text-sm text-white/80">{fmt(selectedSubmission.created_date)}</p>
								</div>
								{#if selectedSubmission.input_type === 'github_repo' || selectedSubmission.input_type === 'github_repo_directory'}
									<div>
										<label class="text-sm text-white/60">Open</label>
										<p class="inline-flex items-center gap-1 text-sm text-white/80">
											<a
												class="underline hover:no-underline"
												href={selectedSubmission.input_content}
												target="_blank"
												rel="noreferrer">Source</a
											>
											<ExternalLink class="h-3 w-3" />
										</p>
									</div>
								{/if}
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
