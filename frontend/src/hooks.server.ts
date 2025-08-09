// src/hooks.server.ts

// [1] Import public environment variables. These are read from your .env at startup.
import { PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';

// [2] Import the Supabase SSR helper that creates a server aware client.
import { createServerClient } from '@supabase/ssr';

// [3] Import SvelteKit types and helpers.
import type { Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { redirect } from '@sveltejs/kit';

// [4] First handle. Its job is to attach a Supabase client and a helper to locals.
const supabaseHandle: Handle = async ({ event, resolve }) => {
    // [5] Build a Supabase client that knows how to read and write cookies on this request.
    event.locals.supabase = createServerClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        cookies: {
            // [6] When Supabase needs to read cookies, we give it all cookies from the request.
            getAll: () => event.cookies.getAll(),
            // [7] When Supabase needs to set or update cookies, we write them to the response.
            setAll: (cookies) => {
                cookies.forEach(({ name, value, options }) => {
                    // [8] Ensure every cookie has a path. Without a path, some clients will not send it back.
                    event.cookies.set(name, value, { ...options, path: '/' });
                });
            }
        }
    });

    // [9] Add a helper to locals that returns a validated session and user.
    //     Validated means we ask Supabase to parse and verify the token from the cookie.
    event.locals.safeGetSession = async () => {
        // [10] First, ask Supabase for the user. This checks the token in the cookie.
        const { data: userData, error: userError } = await event.locals.supabase.auth.getUser();

        // [11] If there is an error, there is no valid token. Return nulls.
        if (userError || !userData.user) {
            return { session: null, user: null };
        }

        // [12] There is a valid user. Now fetch the full session object.
        const { data: sessionData } = await event.locals.supabase.auth.getSession();

        // [13] Return both so server code can rely on them.
        return { session: sessionData.session, user: userData.user };
    };

    // [14] Continue to the rest of the app. Also filter which headers are exposed to the browser.
    //      This avoids leaking internal headers that are only useful server side.
    return resolve(event, {
        filterSerializedResponseHeaders: (name) =>
            name === 'content-range' || name === 'x-supabase-api-version'
    });
};

// [15] Second handle. A simple guard for protected routes.
//      If the user is not logged in, block access to certain paths.
//      If the user is logged in, do not show the login page.
const guardHandle: Handle = async ({ event, resolve }) => {
    // [16] Read the current session once for this request.
    const { session } = await event.locals.safeGetSession();

    // [17] The path the user is trying to visit.
    const path = event.url.pathname;

    // [18] If not logged in and trying to reach protected pages, send to login.
    if (!session && (path === '/submit' || path === '/history')) {
        throw redirect(303, '/login');
    }

    // [19] If already logged in and trying to view the login page, send to home.
    if (session && path === '/login') {
        throw redirect(303, '/');
    }

    // [20] Otherwise let the request continue.
    return resolve(event);
};

// [21] Export a single handle that runs our two pieces in order.
//      First we attach Supabase, then we run the guard.
export const handle: Handle = sequence(supabaseHandle, guardHandle);