import { PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';
import { createBrowserClient } from '@supabase/ssr';
import { browser } from '$app/environment';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ data, depends, fetch }) => {
    // Re-run when auth changes (your layout.svelte calls invalidate('supabase:auth'))
    depends('supabase:auth');

    // Browser Supabase client
    const supabase = createBrowserClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        global: { fetch }
    });

    // Start with what the server provided
    let session = data.session;   // Session | null (from +layout.server.ts)
    let user = data.user;      // User | null (from +layout.server.ts)

    // In the browser, refresh to the most current values
    if (browser) {
        const [{ data: s }, { data: u }] = await Promise.all([
            supabase.auth.getSession(),
            supabase.auth.getUser()
        ]);
        session = s.session ?? null;
        user = u.user ?? null;
    }

    // Return all fields your PageData requires, plus supabase for the client
    return {
        supabase,
        session,
        user
    };
};