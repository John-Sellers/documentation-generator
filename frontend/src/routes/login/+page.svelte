<script>
	export let errors; // to handle errors from actions if needed
	// You could also use a component state to toggle between showing a login vs signup form.
</script>

<h1 class="mb-4 text-2xl font-bold">Sign In or Sign Up</h1>
<form method="POST" action="?/login" class="mb-6">
	<!-- Sign In form -->
	<input type="hidden" name="type" value="login" />
	<div>
		<label>Email</label>
		<input type="email" name="email" required class="input" />
	</div>
	<div>
		<label>Password</label>
		<input type="password" name="password" required class="input" />
	</div>
	<button type="submit" class="btn mt-2">Log In</button>
</form>

<form method="POST" action="?/signup">
	<!-- Sign Up form -->
	<input type="hidden" name="type" value="signup" />
	<div>
		<label>Email</label>
		<input type="email" name="email" required class="input" />
	</div>
	<div>
		<label>Password</label>
		<input type="password" name="password" required class="input" />
	</div>
	<button type="submit" class="btn mt-2">Create Account</button>
</form>

{#if errors}
	<p class="text-red-500">{errors}</p>
{/if}
