// [1] Pull in your public Supabase settings from the environment.
import { PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';

// [2] Bring in the Supabase SSR helper that knows how to work with cookies.
import { createServerClient } from '@supabase/ssr';

// [3] Bring SvelteKit types and helpers that we will use.
import type { Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { redirect } from '@sveltejs/kit';

// [4] This first handle sets up Supabase on every request.
const supabaseHandle: Handle = async ({ event, resolve }) => {
    // [5] Make a Supabase client that can read and write cookies for this request.
    event.locals.supabase = createServerClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY, {
        cookies: {
            // [6] When Supabase asks for cookies, give it the cookies from the request.
            getAll: () => event.cookies.getAll(),
            // [7] When Supabase wants to set cookies, write them onto the response.
            setAll: (cookies) => {
                cookies.forEach(({ name, value, options }) => {
                    // [8] Always force a path so the browser sends the cookie back to us.
                    event.cookies.set(name, value, { ...options, path: '/' });
                });
            }
        }
    });

    // [9] Add a helper that returns a validated user and an optional session token bundle.
    //     Validated means Supabase checks the cookie and confirms it with the auth server.
    event.locals.safeGetSession = async () => {
        // [10] Ask Supabase for the user. This call verifies the cookie with the auth server.
        const { data: userData, error: userError } = await event.locals.supabase.auth.getUser();

        // [11] If there is any error or no user, return user null and session null.
        if (userError || !userData.user) {
            return { user: null, session: null };
        }

        // [12] If you need tokens or expiry times, you can still read the session object.
        //      We will not use session.user anywhere. We only use session for tokens.
        const { data: sessionData } = await event.locals.supabase.auth.getSession();

        // [13] Return the verified user and the session bundle. Never trust session.user.
        return { user: userData.user, session: sessionData.session ?? null };
    };

    // [14] Continue with the request and keep only a few headers visible to the client.
    return resolve(event, {
        filterSerializedResponseHeaders: (name) =>
            name === 'content-range' || name === 'x-supabase-api-version'
    });
};

// [15] This second handle protects routes. It checks the verified user only.
const guardHandle: Handle = async ({ event, resolve }) => {
    // [16] Ask our helper for the verified user and optional session.
    const { user } = await event.locals.safeGetSession();

    // [17] Grab the path the person is visiting.
    const path = event.url.pathname;

    // [18] If there is no user and the path needs auth, send them to login.
    if (!user && (path === '/submit' || path === '/history')) {
        throw redirect(303, '/login');
    }

    // [19] If there is a user and they try to visit the login page, send them home.
    if (user && path === '/login') {
        throw redirect(303, '/');
    }

    // [20] Otherwise let the request continue.
    return resolve(event);
};

// [21] Export the combined handle. First we set up Supabase. Then we guard paths.
export const handle: Handle = sequence(supabaseHandle, guardHandle);