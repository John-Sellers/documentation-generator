<script lang="ts">
	// We import the icon components you already used for your cards.
	// These are normal Svelte components that render simple SVGs.
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

	// We import the enhance helper from SvelteKit.
	// enhance upgrades a normal HTML form so that SvelteKit intercepts the submit event.
	// It still sends a real POST to the server action.
	// It updates this page in place with the action result.
	// The result appears in the special prop named form that SvelteKit injects.
	import { enhance } from '$app/forms';

	// SvelteKit injects a prop named form into this page after an action runs.
	// We declare it here so we can read it.
	// It can hold any JSON shape we choose to return from the server action.
	// Example keys we use in this step are prepareResult and error.
	export let form: any;

	// A simple flag to mimic authentication for now.
	// Your server load function already redirects guests to login.
	// We keep this local flag as a guard placeholder for your current UI.
	let isAuthed = true;

	// A TypeScript union that lists all the submission methods.
	// The value can be one of the string literals below or null before the user chooses.
	type MethodId = 'github_repo' | 'github_repo_directory' | 'zipped_folder' | 'pasted_code' | null;

	// The current method the user has chosen.
	let selectedMethod: MethodId = null;

	// A small bag of local state for inputs and demo flow.
	// These values are bound to inputs so the user sees what they typed.
	// Types are annotated so you know exactly what each field holds.
	let formData = {
		githubUrl: '' as string, // For the repo URL or for the directory page URL
		directoryUrl: '' as string, // You used this earlier as a single field for subdir, we keep it for preview
		codeSnippet: '' as string, // The pasted code text
		file: null as File | null // The uploaded zip file
	};

	// Simple UI flags for spinners and error message boxes.
	let isSubmitting = false; // When true, buttons can show a spinner
	let error = '' as string; // Any human friendly error to render
	// This object was part of your earlier demo flow.
	// We keep it so the rest of your page structure does not break.
	let submission: null | {
		id: number;
		status: 'processing' | 'done';
		input_type: string;
	} = null;

	// The four method cards you already designed.
	// We keep them exactly the same so the grid looks familiar.
	const submissionMethods = [
		{
			id: 'github_repo',
			title: 'GitHub Repository',
			description: 'Analyze an entire GitHub repository',
			icon: Github,
			example: 'https://github.com/owner/repo',
			color: 'from-purple-500 to-blue-500'
		},
		{
			id: 'github_repo_directory',
			title: 'Specific Directory',
			description: 'Focus on a particular folder or subdirectory',
			icon: FolderOpen,
			example: 'https://github.com/owner/repo/tree/main/src',
			color: 'from-blue-500 to-cyan-500'
		},
		{
			id: 'zipped_folder',
			title: 'Upload Files',
			description: 'Upload a ZIP file or provide a ZIP URL',
			icon: Upload,
			example: 'project.zip or https://site.tld/archive.zip',
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

	// You had a combined client side submission function earlier.
	// We keep a trimmed version for non server paths you may still want for demo.
	// The four real server backed forms below no longer depend on this.
	async function handleSubmit() {
		error = '';
		isSubmitting = true;
		try {
			if (!selectedMethod) throw new Error('Please select a submission method');

			// This demo block stays only for non server parts you may want to keep for look and feel.
			// The four real methods now use real HTML forms and the server action.
			submission = {
				id: Date.now(),
				status: 'processing',
				input_type: selectedMethod
			};
			setTimeout(() => {
				if (submission) submission.status = 'done';
			}, 1200);
		} catch (e: any) {
			error = e?.message || 'An error occurred while processing your submission';
		} finally {
			isSubmitting = false;
		}
	}

	// A helper to reset the selection and clear the local inputs.
	function resetForm() {
		selectedMethod = null;
		formData = { githubUrl: '', directoryUrl: '', codeSnippet: '', file: null };
		submission = null;
		error = '';
	}
</script>

{#if !isAuthed}
	<!-- A very simple lock screen when not authenticated. Your server already guards this route. -->
	<div class="flex min-h-screen items-center justify-center p-6">
		<div class="rounded-2xl border border-white/20 bg-white/10 p-6 text-center text-white">
			<p class="mb-4">You must be signed in to submit</p>
			<a href="/" class="rounded bg-white/20 px-4 py-2 hover:bg-white/30">Go Home</a>
		</div>
	</div>
{:else if submission && submission.status === 'processing'}
	<!-- A small processing screen from your original file. -->
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
	<!-- Main container and max width wrapper for your content. -->
	<div class="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
		<div class="mx-auto max-w-4xl">
			{#if !selectedMethod}
				<!-- Landing header with icon and title. -->
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

				<!-- Error box if a local error existed from the demo path. -->
				{#if error}
					<div
						class="mb-6 flex items-start gap-3 rounded-xl border border-red-300/50 bg-red-500/20 p-4 text-white"
					>
						<AlertCircle class="mt-0.5 h-5 w-5" />
						<div>{error}</div>
					</div>
				{/if}

				<!-- The four method choice cards. Each button sets selectedMethod. -->
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
				<!-- Back button to return to the method grid. -->
				<div class="mb-6">
					<button
						class="inline-flex items-center gap-2 rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm hover:bg-white/20"
						on:click={resetForm}
					>
						<ArrowLeft class="h-4 w-4" />
						Back to Submission Methods
					</button>
				</div>

				<!-- A top banner that restates the chosen method with its icon and text. -->
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

				<!-- Card that holds the method specific form and any results from the server. -->
				<div class="mt-6 rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md">
					<div class="space-y-6 p-6">
						{#if selectedMethod === 'github_repo'}
							<!-- GitHub repository form posts to the named action prepare. -->
							<!-- The server action requires repo_ref to be present. The input is required here. -->
							<form method="post" action="?/prepare" use:enhance>
								<!-- This hidden input tells the server which branch of the action to run. -->
								<input type="hidden" name="input_type" value="github_repo" />

								<label class="mb-2 block font-medium text-white" for="repo_url"
									>GitHub Repository URL</label
								>
								<input
									id="repo_url"
									name="github_url"
									class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
									placeholder="https://github.com/owner/repo"
									bind:value={formData.githubUrl}
									required
								/>

								<div class="mt-3">
									<label class="mb-2 block font-medium text-white" for="repo_ref"
										>Branch or tag or commit</label
									>
									<input
										id="repo_ref"
										name="repo_ref"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="main"
										required
									/>
								</div>

								<div class="mt-3">
									<label class="mb-2 block font-medium text-white" for="display_name_repo"
										>Optional display name</label
									>
									<input
										id="display_name_repo"
										name="display_name"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="Example: repo summary"
									/>
								</div>

								<div class="mt-4">
									<button
										type="submit"
										class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600"
									>
										<CheckCircle2 class="h-4 w-4" />
										<span>Prepare from GitHub repository</span>
									</button>
								</div>
							</form>
						{/if}

						{#if selectedMethod === 'github_repo_directory'}
							<!-- GitHub directory form accepts a full directory URL like owner slash repo slash tree slash ref slash subdir. -->
							<!-- The server action will parse the URL into repo_url, repo_ref, and subdir. -->
							<!-- We also collect repo_ref explicitly and make it required. Your server action uses the value from this field. -->
							<form method="post" action="?/prepare" use:enhance>
								<input type="hidden" name="input_type" value="github_repo_directory" />

								<label class="mb-2 block font-medium text-white" for="directory_url"
									>GitHub Directory URL</label
								>
								<input
									id="directory_url"
									name="directory_url"
									class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
									placeholder="https://github.com/owner/repo/tree/main/src"
									bind:value={formData.directoryUrl}
									required
								/>

								<div class="mt-3">
									<label class="mb-2 block font-medium text-white" for="repo_ref_dir"
										>Branch or tag or commit</label
									>
									<input
										id="repo_ref_dir"
										name="repo_ref"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="main"
										required
									/>
								</div>

								<div class="mt-3">
									<label class="mb-2 block font-medium text-white" for="display_name_dir"
										>Optional display name</label
									>
									<input
										id="display_name_dir"
										name="display_name"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="Example: focus on slash src"
									/>
								</div>

								<div class="mt-4">
									<button
										type="submit"
										class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600"
									>
										<CheckCircle2 class="h-4 w-4" />
										<span>Prepare from GitHub repository directory</span>
									</button>
								</div>
							</form>
						{/if}

						{#if selectedMethod === 'zipped_folder'}
							<!-- Zipped folder form supports two paths. -->
							<!-- If the user uploads a file named zip_file then the server sends multipart. -->
							<!-- If the user enters a zip_url then the server sends JSON. -->
							<form method="post" action="?/prepare" enctype="multipart/form-data" use:enhance>
								<input type="hidden" name="input_type" value="zipped_folder" />

								<label class="mb-2 block font-medium text-white" for="zip_file"
									>Upload ZIP file</label
								>
								<input
									id="zip_file"
									name="zip_file"
									type="file"
									accept=".zip"
									class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm file:mr-3 file:rounded-md file:border-0 file:bg-white/20 file:px-3 file:py-2 file:text-white"
								/>
								<p class="mt-2 text-sm text-white/60">Leave the URL empty if you upload a file.</p>

								<div class="mt-3">
									<label class="mb-2 block font-medium text-white" for="zip_url">ZIP file URL</label
									>
									<input
										id="zip_url"
										name="zip_url"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="https://example.com/archive.zip"
									/>
								</div>

								<div class="mt-3">
									<label class="mb-2 block font-medium text-white" for="display_name_zip"
										>Optional display name</label
									>
									<input
										id="display_name_zip"
										name="display_name"
										class="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white backdrop-blur-sm placeholder:text-white/50"
										placeholder="Example: backend source zip"
									/>
								</div>

								<div class="mt-4">
									<button
										type="submit"
										class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600"
									>
										<CheckCircle2 class="h-4 w-4" />
										<span>Prepare from ZIP file</span>
									</button>
								</div>
							</form>
						{/if}

						{#if selectedMethod === 'pasted_code'}
							<!-- Pasted code form. Sends JSON with input_type pasted_code and the code_snippet text. -->
							<form method="post" action="?/prepare" use:enhance>
								<input type="hidden" name="input_type" value="pasted_code" />

								<label class="mb-2 block font-medium text-white" for="code_snippet"
									>Code Snippet</label
								>
								<textarea
									id="code_snippet"
									name="code_snippet"
									class="min-h-[200px] w-full rounded border border-white/30 bg-white/10 px-3 py-2 font-mono text-sm text-white backdrop-blur-sm placeholder:text-white/50"
									placeholder="Paste your code here"
									bind:value={formData.codeSnippet}
									required
								>
								</textarea>

								<div class="mt-4">
									<button
										type="submit"
										class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600"
									>
										<CheckCircle2 class="h-4 w-4" />
										<span>Prepare pasted code</span>
									</button>
								</div>
							</form>

							{#if formData.codeSnippet.trim()}
								<pre
									class="mt-3 overflow-auto rounded bg-black/30 p-3 text-xs">{formData.codeSnippet}</pre>
							{/if}
						{/if}

						<!-- Server action results. These blocks render after any prepare form posts. -->
						{#if form?.prepareResult}
							<hr class="my-6 border-white/20" />
							<h2 class="mb-2 text-xl font-semibold text-white">Prepare result</h2>
							<p class="mb-2 text-white/70">
								This is the raw JSON that came back from your Modal prepare endpoint.
							</p>
							<pre class="overflow-auto rounded bg-black/30 p-3 text-xs text-white">
{JSON.stringify(form.prepareResult, null, 2)}
              </pre>
						{/if}

						{#if form?.error}
							<div
								class="mt-4 flex items-start gap-3 rounded-xl border border-red-300/50 bg-red-500/20 p-4 text-white"
							>
								<AlertCircle class="mt-0.5 h-5 w-5" />
								<div>{form.error}</div>
							</div>
						{/if}

						<!-- Keep your original all in one button for any future demo needs. -->
						{#if selectedMethod !== 'pasted_code' && selectedMethod !== 'github_repo' && selectedMethod !== 'github_repo_directory' && selectedMethod !== 'zipped_folder'}
							<button
								class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600 disabled:opacity-60"
								on:click|preventDefault={handleSubmit}
								disabled={isSubmitting}
							>
								{#if isSubmitting}
									<Loader2 class="h-4 w-4 animate-spin" />
									<span>Processing</span>
								{:else}
									<CheckCircle2 class="h-4 w-4" />
									<span>Generate Business Summary</span>
								{/if}
							</button>
						{/if}
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
