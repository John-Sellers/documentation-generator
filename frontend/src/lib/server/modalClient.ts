// src/lib/server/modalClient.ts

// Line 1: We import private env values from SvelteKit.
// Line 2: These values are loaded at build time and exist only on the server.
// Line 3: This is safer than using process.env directly.
import {
    MODAL_PREPARE_URL as ENV_MODAL_PREPARE_URL,   // Line 4: The prepare endpoint URL from .env
    MODAL_SUMMARIZE_URL as ENV_MODAL_SUMMARIZE_URL, // Line 5: The summarize endpoint URL from .env
    MODAL_SECRET_TOKEN as ENV_MODAL_SECRET_TOKEN    // Line 6: The optional secret token from .env
} from '$env/static/private';

// Line 7: This helper checks if the env variables exist.
// Line 8: It does not talk to Modal. It only inspects local config.
export function checkModalEnv() {
    // Line 9: We collect any missing names here for a helpful message.
    const missing: string[] = [];

    // Line 10: If the prepare URL is empty, we add its name to missing.
    if (!ENV_MODAL_PREPARE_URL) missing.push('MODAL_PREPARE_URL');

    // Line 11: If the summarize URL is empty, we add its name to missing.
    if (!ENV_MODAL_SUMMARIZE_URL) missing.push('MODAL_SUMMARIZE_URL');

    // Line 12: The token can be empty. That is allowed. We do not mark it missing.

    // Line 13: We return a simple object with status and safe previews.
    return {
        // Line 14: ok is true if nothing is missing.
        ok: missing.length === 0,

        // Line 15: This is the list of missing names to show the user if any.
        missing,

        // Line 16: values holds safe debug info to help you see what is set.
        values: {
            // Line 17: It is safe to show URLs since they do not contain secrets.
            MODAL_PREPARE_URL: ENV_MODAL_PREPARE_URL ?? null,

            // Line 18: Same for summarize URL.
            MODAL_SUMMARIZE_URL: ENV_MODAL_SUMMARIZE_URL ?? null,

            // Line 19: True means a token string is present. False means no token set.
            MODAL_SECRET_TOKEN_present: !!ENV_MODAL_SECRET_TOKEN,

            // Line 20: If a token exists, we show the first four characters only.
            // Line 21: This helps you confirm the correct token is loaded without exposing it.
            MODAL_SECRET_TOKEN_preview: ENV_MODAL_SECRET_TOKEN
                ? ENV_MODAL_SECRET_TOKEN.slice(0, 4) + '***'
                : null
        }
    };
}

// Line 22: Later, we will add real server fetch helpers here.
// Line 23: By keeping all Modal calls in one place, swapping to Vercel AI Gateway later is easy.