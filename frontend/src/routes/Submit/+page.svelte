<script lang="ts">
	import {
		Github,
		FolderOpen,
		Upload,
		Code,
		Loader2,
		CheckCircle2,
		AlertCircle,
		ArrowLeft
	} from '@lucide/svelte';

	// Simple auth check you can replace later
	// If you want to block the page when logged out, toggle this to false
	let isAuthed = true;

	// UI state
	type MethodId = 'github_repo' | 'github_repo_directory' | 'zipped_folder' | 'pasted_code' | null;
	let selectedMethod: MethodId = null;

	let formData = {
		githubUrl: '',
		directoryUrl: '',
		codeSnippet: '',
		file: null as File | null
	};

	let isSubmitting = false;
	let error = '';
	let submission: null | { id: number; status: 'processing' | 'done'; input_type: string } = null;

	// Cards shown on the first screen
	const submissionMethods = [
		{
			id: 'github_repo',
			title: 'GitHub Repository',
			description: 'Analyze an entire GitHub repository',
			icon: Github,
			example: 'https://github.com/username/repository',
			color: 'from-purple-500 to-blue-500'
		},
		{
			id: 'github_repo_directory',
			title: 'Specific Directory',
			description: 'Focus on a particular folder or subdirectory',
			icon: FolderOpen,
			example: 'https://github.com/username/repo/tree/main/src',
			color: 'from-blue-500 to-cyan-500'
		},
		{
			id: 'zipped_folder',
			title: 'Upload Files',
			description: 'Upload a ZIP file or folder',
			icon: Upload,
			example: 'project.zip, source-code.zip',
			color: 'from-cyan-500 to-teal-500'
		},
		{
			id: 'pasted_code',
			title: 'Code Snippet',
			description: 'Paste code directly for analysis',
			icon: Code,
			example: 'function calculateTotal() { ... }',
			color: 'from-teal-500 to-green-500'
		}
	] as const;

	// Tiny helpers that replace your old Submission.create and UploadFile
	async function fakeUploadFile(file: File) {
		await new Promise((r) => setTimeout(r, 600));
		return { file_url: URL.createObjectURL(file) }; // local object url for demo
	}

	async function fakeCreateSubmission(payload: {
		input_type: string;
		input_content: string;
		original_filename: string;
	}) {
		await new Promise((r) => setTimeout(r, 400));
		return { id: Date.now(), status: 'processing' as const, ...payload };
	}

	async function handleSubmit() {
		error = '';
		isSubmitting = true;

		try {
			if (!selectedMethod) throw new Error('Please select a submission method');

			let inputContent = '';
			let originalFilename = '';

			if (selectedMethod === 'github_repo') {
				if (!formData.githubUrl || !formData.githubUrl.includes('github.com')) {
					throw new Error('Please enter a valid GitHub repository URL');
				}
				inputContent = formData.githubUrl;
			}

			if (selectedMethod === 'github_repo_directory') {
				if (!formData.directoryUrl || !formData.directoryUrl.includes('github.com')) {
					throw new Error('Please enter a valid GitHub directory URL');
				}
				inputContent = formData.directoryUrl;
			}

			if (selectedMethod === 'zipped_folder') {
				if (!formData.file) throw new Error('Please select a file to upload');
				const uploadResult = await fakeUploadFile(formData.file);
				inputContent = uploadResult.file_url;
				originalFilename = formData.file.name;
			}

			if (selectedMethod === 'pasted_code') {
				if (!formData.codeSnippet.trim()) {
					throw new Error('Please paste some code to analyze');
				}
				inputContent = formData.codeSnippet;
			}

			// Create submission record
			const rec = await fakeCreateSubmission({
				input_type: selectedMethod,
				input_content: inputContent,
				original_filename: originalFilename
			});
			submission = rec;

			// Send to webhook example
			// Replace this with your real endpoint when ready
			await fetch('https://httpbin.org/post', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					submission_id: rec.id,
					input_type: selectedMethod,
					input_content: inputContent,
					original_filename: originalFilename
				})
			});

			// Simulate processing finishing
			setTimeout(() => {
				if (submission) submission.status = 'done';
			}, 1500);
		} catch (e: any) {
			error = e?.message || 'An error occurred while processing your submission';
		} finally {
			isSubmitting = false;
		}
	}

	function resetForm() {
		selectedMethod = null;
		formData = { githubUrl: '', directoryUrl: '', codeSnippet: '', file: null };
		submission = null;
		error = '';
	}
</script>

{#if !isAuthed}
	<!-- Simple guard. Replace with your real auth handling later -->
	<div class="flex min-h-screen items-center justify-center p-6">
		<div class="rounded-2xl border border-white/20 bg-white/10 p-6 text-center text-white">
			<p class="mb-4">You must be signed in to submit</p>
			<a href="/Home" class="rounded bg-white/20 px-4 py-2 hover:bg-white/30">Go Home</a>
		</div>
	</div>
{:else if submission && submission.status === 'processing'}
	<!-- Processing screen -->
	<div class="flex min-h-screen items-center justify-center p-6">
		<div
			class="space-y-4 rounded-2xl border border-white/20 bg-white/10 p-8 text-center text-white"
		>
			<Loader2 class="mx-auto h-8 w-8 animate-spin" />
			<div class="text-lg">We are processing your submission</div>
			<button class="rounded bg-white/20 px-4 py-2 hover:bg-white/30" on:click={resetForm}>
				Cancel
			</button>
		</div>
	</div>
{:else}
	<div class="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
		<div class="mx-auto max-w-4xl">
			{#if !selectedMethod}
				<!-- Header -->
				<div class="mb-12 text-center">
					<div class="mb-6 inline-flex items-center gap-3">
						<div
							class="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/30 bg-white/20 bg-gradient-to-r from-purple-500 to-pink-500 backdrop-blur-sm"
						>
							<Code class="h-8 w-8 text-white" />
						</div>
					</div>
					<h1 class="mb-4 text-4xl font-bold text-white">Transform Code into Business Insights</h1>
					<p class="mx-auto max-w-2xl text-xl leading-relaxed text-white/80">
						Submit your code and get clear, non technical summaries of the business problems it
						solves
					</p>
				</div>

				{#if error}
					<div
						class="mb-6 flex items-start gap-3 rounded-xl border border-red-300/50 bg-red-500/20 p-4 text-white"
					>
						<AlertCircle class="mt-0.5 h-5 w-5" />
						<div>{error}</div>
					</div>
				{/if}

				<!-- Submission method cards -->
				<div class="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2">
					{#each submissionMethods as method}
						<button
							class="flex items-center gap-4 rounded-2xl border border-white/20 bg-white/10 p-5 text-left backdrop-blur-md transition hover:bg-white/15"
							on:click={() => (selectedMethod = method.id as MethodId)}
						>
							<div
								class={'h-12 w-12 bg-gradient-to-r ' +
									method.color +
									' flex items-center justify-center rounded-xl'}
							>
								<svelte:component this={method.icon} class="h-6 w-6 text-white" />
							</div>
							<div>
								<div class="font-semibold text-white">{method.title}</div>
								<div class="text-sm text-white/70">{method.description}</div>
								<div class="mt-1 text-xs text-white/50">Example: {method.example}</div>
							</div>
						</button>
					{/each}
				</div>
			{:else}
				<!-- Selected method header -->
				<div class="mb-6">
					<button
						class="inline-flex items-center gap-2 rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm hover:bg-white/20"
						on:click={resetForm}
					>
						<ArrowLeft class="h-4 w-4" />
						Back to Submission Methods
					</button>
				</div>

				<div class="space-y-6">
					<div class="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md">
						<div class="rounded-t-2xl border-b border-white/10 px-6 py-4">
							<div class="flex items-center gap-3">
								{#if selectedMethod}
									{#each submissionMethods as m}
										{#if m.id === selectedMethod}
											<div
												class={'h-10 w-10 bg-gradient-to-r ' +
													m.color +
													' flex items-center justify-center rounded-lg'}
											>
												<svelte:component this={m.icon} class="h-5 w-5 text-white" />
											</div>
											<div>
												<div class="font-semibold text-white">{m.title}</div>
												<div class="text-sm text-white/60">{m.description}</div>
											</div>
										{/if}
									{/each}
								{/if}
							</div>
						</div>
					</div>

					<!-- Input form -->
					<div class="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md">
						<div class="space-y-6 p-6">
							{#if selectedMethod === 'github_repo'}
								<div>
									<label class="mb-2 block font-medium text-white">GitHub Repository URL</label>
									<input
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="https://github.com/username/repository"
										bind:value={formData.githubUrl}
									/>
									<p class="mt-2 text-sm text-white/60">
										Example: https://github.com/facebook/react
									</p>
								</div>
							{/if}

							{#if selectedMethod === 'github_repo_directory'}
								<div>
									<label class="mb-2 block font-medium text-white">GitHub Directory URL</label>
									<input
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="https://github.com/username/repo/tree/main/src"
										bind:value={formData.directoryUrl}
									/>
									<p class="mt-2 text-sm text-white/60">
										Example: https://github.com/vercel/next.js/tree/canary/packages/next/src
									</p>
								</div>
							{/if}

							{#if selectedMethod === 'zipped_folder'}
								<div>
									<label class="mb-2 block font-medium text-white">Upload ZIP File</label>
									<input
										type="file"
										accept=".zip,.rar,.7z"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm file:mr-3 file:rounded-md file:border-0 file:bg-white/20 file:px-3 file:py-2 file:text-white"
										on:change={(e) => {
											const files = (e.target as HTMLInputElement).files;
											formData.file = files && files[0] ? files[0] : null;
										}}
									/>
									<p class="mt-2 text-sm text-white/60">
										Supported formats: ZIP, RAR, 7Z. Max 50 MB
									</p>
								</div>
							{/if}

							{#if selectedMethod === 'pasted_code'}
								<div>
									<label class="mb-2 block font-medium text-white">Code Snippet</label>
									<textarea
										class="min-h-[200px] w-full rounded border border-white/30 bg-white/10 px-3 py-2 font-mono text-sm text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="Paste your code here..."
										bind:value={formData.codeSnippet}
									/>
									<!-- Simple preview -->
									{#if formData.codeSnippet.trim()}
										<pre
											class="mt-3 overflow-auto rounded bg-black/30 p-3 text-xs">{formData.codeSnippet}</pre>
									{/if}
								</div>
							{/if}

							<button
								class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600 disabled:opacity-60"
								on:click|preventDefault={handleSubmit}
								disabled={isSubmitting}
							>
								{#if isSubmitting}
									<Loader2 class="h-4 w-4 animate-spin" />
									<span>Processing...</span>
								{:else}
									<CheckCircle2 class="h-4 w-4" />
									<span>Generate Business Summary</span>
								{/if}
							</button>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
