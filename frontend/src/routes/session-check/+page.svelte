<script lang="ts">
	// [1] `data` is whatever the server load returned above.
	export let data: { hasSession: boolean; email: string | null };
</script>

<!-- [2] A friendly heading -->
<h1 class="mb-4 text-2xl font-semibold">Session check</h1>

<!-- [3] If you are logged in, show green and the email. Otherwise show red. -->
{#if data.hasSession}
	<p class="text-green-600">You are logged in as {data.email}</p>
{:else}
	<p class="text-red-600">No active session</p>
{/if}
