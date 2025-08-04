<script lang="ts">
	let projectPath = '';
	let isLoading = false;
	let summary = '';

	async function submitForm() {
		isLoading = true;
		summary = '';

		try {
			const res = await fetch(import.meta.env.PUBLIC_SUMMARY_API, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: 'Bearer ' + 'Pus2lyA0Iyj3^ah%xKoE3zvg' // Replace with real token if needed
				},
				body: JSON.stringify({ project_path: projectPath })
			});

			if (!res.ok) {
				throw new Error(`Server error ${res.status}`);
			}

			const data = await res.json();
			summary = data.summary || JSON.stringify(data, null, 2);
		} catch (error: unknown) {
			if (error instanceof Error) {
				summary = '❌ Failed to fetch summary: ' + error.message;
			} else {
				summary = '❌ Unknown error occurred.';
			}
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="mx-auto max-w-xl space-y-6 rounded-xl bg-white p-6 shadow-md">
		<h1 class="text-2xl font-bold text-gray-800">Summarize Project</h1>

		<form on:submit|preventDefault={submitForm} class="space-y-4">
			<label class="block">
				<span class="font-medium text-gray-700">Project Path</span>
				<textarea
					bind:value={projectPath}
					class="mt-1 block w-full rounded-md border border-gray-300 p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
					rows="3"
					placeholder="/workspaces/my-project"
				></textarea>
			</label>

			<button
				type="submit"
				class="rounded-md bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
				disabled={isLoading}
			>
				{isLoading ? 'Summarizing...' : 'Summarize'}
			</button>
		</form>

		{#if summary}
			<div class="whitespace-pre-wrap rounded-md border border-gray-300 bg-gray-100 p-4">
				{summary}
			</div>
		{/if}
	</div>
</div>
