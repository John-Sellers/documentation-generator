// [1] Pull your public Supabase settings from the environment for the browser client.
import { PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';

// [2] Bring in the browser Supabase helper.
import { createBrowserClient } from '@supabase/ssr';

// [3] Ask SvelteKit if we are in the browser or on the server.
import { browser } from '$app/environment';

// [4] Type for the load function. This runs in the browser for your root layout.
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ data, depends, fetch }) => {
    // [5] Tell SvelteKit to rerun this loader when auth changes.
    //     Your layout.svelte will call invalidate with this same key.
    depends('supabase:auth');

    // [6] Make a browser Supabase client and hand it the fetch function.
    const supabase = createBrowserClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        global: { fetch }
    });

    // [7] Start with the values the server gave us.
    //     These came from +layout.server.ts which called event.locals.safeGetSession.
    let session = data.session; // may be null. Do not use session.user.
    let user = data.user;       // may be null. This came from getUser on the server.

    // [8] In the browser, refresh to the most current and verified user.
    //     We do not read session.user. We only read the user from getUser.
    if (browser) {
        // [9] Ask for the verified user from the auth server.
        const { data: u } = await supabase.auth.getUser();

        // [10] Optionally refresh the session tokens. This is safe as long as we never use session.user.
        const { data: s } = await supabase.auth.getSession();

        // [11] Update our local copies. user comes only from getUser.
        user = u.user ?? null;
        session = s.session ?? null; // keep if you need access_token or expires_at elsewhere
    }

    // [12] Hand values to the page. supabase for client calls, plus user and session.
    //      Your components should read only user for identity and permissions.
    return {
        supabase,
        session, // do not use session.user
        user
    };
};