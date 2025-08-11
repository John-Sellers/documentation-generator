<script lang="ts">
	// We will use SvelteKit navigation to move to /submit after success
	import { goto } from '$app/navigation';

	// We receive data from the root layout loads
	// data.supabase is the browser client created in +layout.ts
	// data.session is the current session if the user is already signed in
	import type { Session } from '@supabase/supabase-js';
	export let data: { supabase: any; session: Session | null };

	// Local UI state for this page
	// mode chooses which form we show
	let mode: 'login' | 'signup' = 'login';
	// simple two inputs bound to text fields
	let email = '';
	let password = '';
	// flags and messages for UX
	let loading = false;
	let errorMsg: string | null = null;
	let infoMsg: string | null = null;

	// Small helper to switch between the two forms
	// We also clear messages to avoid confusion
	function switchMode(next: 'login' | 'signup') {
		mode = next;
		errorMsg = null;
		infoMsg = null;
	}

	// Create a new account with email and password
	// If your Supabase project has email confirmation on
	// the user must click the link that is sent by email
	// That link will send the browser to /submit so the user lands on the right page
	async function handleSignup() {
		errorMsg = null;
		infoMsg = null;
		loading = true;
		try {
			const { data: signupData, error } = await data.supabase.auth.signUp({
				email,
				password,
				options: {
					// After the user clicks the email link, come back to /submit
					// Your server hook will read the new session cookie on the next request
					emailRedirectTo: `${location.origin}/submit`
				}
			});

			// If Supabase returns an error, show it
			if (error) {
				errorMsg = error.message;
				return;
			}

			// If confirmation is disabled, Supabase may create a session right away
			// In that case we can send the user to /submit immediately
			if (signupData.session) {
				await goto('/submit');
				return;
			}

			// If confirmation is required there is no session yet
			// Tell the user to check email for the link
			infoMsg = 'Check your email and click the confirmation link to finish sign up.';
		} catch (e: any) {
			errorMsg = e?.message ?? 'Something went wrong during sign up.';
		} finally {
			loading = false;
		}
	}

	// Log in an existing user with email and password
	// On success we navigate to /submit right away
	async function handleLogin() {
		errorMsg = null;
		infoMsg = null;
		loading = true;
		try {
			const { error } = await data.supabase.auth.signInWithPassword({
				email,
				password
			});

			// Wrong email or password will come back as an error
			if (error) {
				errorMsg = error.message;
				return;
			}

			// Success. The supabase client updates the session in the browser
			// Our root layout listener will refresh session data
			// We also navigate to /submit so the user lands where you want
			await goto('/submit');
		} catch (e: any) {
			errorMsg = e?.message ?? 'Something went wrong during login.';
		} finally {
			loading = false;
		}
	}

	// Convenience flag in case the user somehow reaches this page while already signed in
	// Your server side guard should also redirect signed in users away from /login
	$: alreadySignedIn = Boolean(data.session);
</script>

<!-- Page shell -->
<div class="mx-auto max-w-md p-6 text-white">
	<h1 class="mb-6 text-3xl font-semibold">Login or Sign up</h1>

	<!-- If there is already a session, show a friendly note -->
	{#if alreadySignedIn}
		<div class="mb-4 rounded border border-emerald-400/30 bg-emerald-500/10 p-3 text-emerald-200">
			You are already signed in.
		</div>
	{/if}

	<!-- Toggle buttons to switch between forms -->
	<div class="mb-6 inline-flex rounded-lg border border-white/20 bg-white/10">
		<button
			type="button"
			class={'px-4 py-2 text-sm ' + (mode === 'login' ? 'bg-white/20 font-medium' : 'opacity-80')}
			on:click={() => switchMode('login')}
			disabled={loading}
		>
			Login
		</button>
		<button
			type="button"
			class={'px-4 py-2 text-sm ' + (mode === 'signup' ? 'bg-white/20 font-medium' : 'opacity-80')}
			on:click={() => switchMode('signup')}
			disabled={loading}
		>
			Sign up
		</button>
	</div>

	<!-- Shared email field -->
	<div class="mb-3">
		<label class="mb-1 block text-sm text-white/80">Email</label>
		<input
			type="email"
			class="w-full rounded bg-white/10 px-3 py-2 outline-none ring-1 ring-white/20 focus:ring-2 focus:ring-sky-400"
			bind:value={email}
			required
			autocomplete="email"
			placeholder="you@example.com"
			disabled={loading}
		/>
	</div>

	<!-- Shared password field -->
	<div class="mb-4">
		<label class="mb-1 block text-sm text-white/80">Password</label>
		<input
			type="password"
			class="w-full rounded bg-white/10 px-3 py-2 outline-none ring-1 ring-white/20 focus:ring-2 focus:ring-sky-400"
			bind:value={password}
			required
			autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
			placeholder={mode === 'login' ? 'Your password' : 'Create a strong password'}
			disabled={loading}
		/>
	</div>

	<!-- Primary action button changes by mode -->
	{#if mode === 'login'}
		<button
			class="w-full rounded bg-sky-500 px-4 py-2 font-medium hover:bg-sky-600 disabled:opacity-50"
			on:click|preventDefault={handleLogin}
			disabled={loading}
		>
			{#if loading}Logging in...{:else}Log in{/if}
		</button>
	{:else}
		<button
			class="w-full rounded bg-indigo-500 px-4 py-2 font-medium hover:bg-indigo-600 disabled:opacity-50"
			on:click|preventDefault={handleSignup}
			disabled={loading}
		>
			{#if loading}Creating account...{:else}Create account{/if}
		</button>
	{/if}

	<!-- Error and info messages for the user -->
	{#if errorMsg}
		<div class="mt-4 rounded border border-rose-400/30 bg-rose-500/10 p-3 text-rose-200">
			{errorMsg}
		</div>
	{/if}

	{#if infoMsg}
		<div class="mt-4 rounded border border-amber-400/30 bg-amber-500/10 p-3 text-amber-200">
			{infoMsg}
		</div>
	{/if}

	<!-- Small hint for new users -->
	<p class="mt-6 text-sm text-white/60">
		If your project uses email confirmation, check your inbox for a link. After you click it, you
		will land on the Submit page.
	</p>
</div>
