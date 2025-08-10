// frontend/src/routes/api/summarizer/health/+server.ts

// Import this because the code needs to read server-only environment variables at build time.
// $env/static/private only works on the server and never ships to the browser.
import { MODAL_SUMMARIZER_URL, MODAL_SUMMARIZER_TOKEN } from '$env/static/private';

// Import this because SvelteKit needs a typed RequestHandler for server routes.
import type { RequestHandler } from '@sveltejs/kit';

/**
 * GET /api/summarizer/health
 *
 * Purpose:
 * - Call this request to verify that the backend can see the Modal URL and secret token.
 * - Return only booleans so nothing sensitive is leaked.
 * - Avoid calling the real Modal endpoint yet; this is a config sanity check.
 */
export const GET: RequestHandler = async () => {
    // Compute a minimal, non-sensitive status object.
    // hasUrl indicates whether the string looks non-empty.
    // hasToken indicates whether the token string looks non-empty.
    // The actual values are never returned.
    const status = {
        hasUrl: typeof MODAL_SUMMARIZER_URL === 'string' && MODAL_SUMMARIZER_URL.length > 0,
        hasToken: typeof MODAL_SUMMARIZER_TOKEN === 'string' && MODAL_SUMMARIZER_TOKEN.length > 0
    };

    // If either value is missing, respond with 500 to make the failure obvious in the browser/console.
    if (!status.hasUrl || !status.hasToken) {
        return new Response(JSON.stringify(status), {
            status: 500,
            headers: { 'content-type': 'application/json' }
        });
    }

    // Otherwise respond 200 OK with the safe status booleans.
    return new Response(JSON.stringify(status), {
        status: 200,
        headers: { 'content-type': 'application/json' }
    });
};