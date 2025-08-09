// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

// src/app.d.ts

// [1] We import Supabase types so we can precisely describe what we attach to SvelteKit.
import type { SupabaseClient, Session, User } from '@supabase/supabase-js';

// [2] We are extending SvelteKit's global App namespace to add our own types.
//     This file never runs in the browser. It only helps TypeScript understand shapes.
declare global {
	namespace App {
		// [3] Locals is a per request storage on the server.
		//     Anything you put here is available during that single request.
		interface Locals {
			// [4] We will place a Supabase client on locals for this request.
			supabase: SupabaseClient;

			// [5] We will also place a helper function that fetches a validated session and user.
			//     If the user is not logged in, both are null.
			safeGetSession: () => Promise<{ session: Session | null; user: User | null }>;
		}

		// [6] PageData is what load functions return and your components receive as `data`.
		//     We include session and user so the UI can react to login state.
		interface PageData {
			session: Session | null;
			user: User | null;
		}
	}
}

// [7] This empty export keeps TypeScript happy inside a .d.ts file.
export { };

