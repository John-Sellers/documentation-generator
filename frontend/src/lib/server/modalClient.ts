// We import private server only environment variables the SvelteKit way.
// $env/static/private reads values at build time and only exposes them on the server.
// We alias them to names with ENV_ prefix to make it obvious these are raw env values.
import {
    MODAL_PREPARE_URL as ENV_MODAL_PREPARE_URL,    // string | undefined. The prepare endpoint base URL from .env
    MODAL_SUMMARIZE_URL as ENV_MODAL_SUMMARIZE_URL, // string | undefined. The summarize endpoint base URL from .env
    MODAL_SECRET_TOKEN as ENV_MODAL_SECRET_TOKEN    // string | undefined. Optional secret token for Authorization header
} from '$env/static/private';

/**
 * checkModalEnv
 * Purpose: verify that required env values exist so routes can fail fast with a helpful message.
 * Returns: a plain object with:
 *  - ok: boolean. true when nothing is missing.
 *  - missing: string[]. names of any missing env vars.
 *  - values: small redacted previews to help debugging without leaking secrets.
 */
export function checkModalEnv() {
    // Collect the names of any missing values.
    const missing: string[] = [];

    // If a value is empty, push its variable name so the caller can show a clear error.
    if (!ENV_MODAL_PREPARE_URL) missing.push('MODAL_PREPARE_URL');
    if (!ENV_MODAL_SUMMARIZE_URL) missing.push('MODAL_SUMMARIZE_URL');
    // Token is optional, so we do not mark it missing.

    // Return a simple diagnostic object.
    return {
        ok: missing.length === 0,
        missing,
        values: {
            // Safe to echo URLs in diagnostics. They do not contain secrets.
            MODAL_PREPARE_URL: ENV_MODAL_PREPARE_URL ?? null,
            MODAL_SUMMARIZE_URL: ENV_MODAL_SUMMARIZE_URL ?? null,
            // For tokens, only state if present and show a tiny preview.
            MODAL_SECRET_TOKEN_present: !!ENV_MODAL_SECRET_TOKEN,
            MODAL_SECRET_TOKEN_preview: ENV_MODAL_SECRET_TOKEN
                ? ENV_MODAL_SECRET_TOKEN.slice(0, 4) + '***'
                : null
        }
    };
}

/**
 * postJsonToModal<TReq, TRes>
 * Purpose: send a JSON POST to a Modal endpoint on the server.
 * Generics:
 *  - TReq is the TypeScript type of the request body you pass in.
 *  - TRes is the TypeScript type you want back. Use unknown if you just want raw JSON.
 * Parameters:
 *  - url: string. The full URL to call. Example: ENV_MODAL_PREPARE_URL
 *  - body: TReq. The plain object that will be JSON.stringify-ed into the request body.
 * Returns:
 *  - Promise<TRes>. The response parsed as JSON and cast to TRes (your chosen type).
 * Throws:
 *  - Error if the HTTP status is not ok. Includes status code and response text to help debugging.
 */
export async function postJsonToModal<TReq extends object, TRes = unknown>(
    url: string,
    body: TReq
): Promise<TRes> {
    // We build standard JSON headers.
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };

    // If a token exists, attach a Bearer Authorization header.
    if (ENV_MODAL_SECRET_TOKEN && ENV_MODAL_SECRET_TOKEN.trim().length > 0) {
        headers.Authorization = `Bearer ${ENV_MODAL_SECRET_TOKEN}`;
    }

    // Make the server side HTTP POST call.
    const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    });

    // If status is not in the 200 to 299 range, throw with details.
    if (!res.ok) {
        const text = await res.text().catch(() => '<no body>');
        throw new Error(`Modal JSON request failed with ${res.status}: ${text}`);
    }

    // Parse JSON response and return it.
    const data = (await res.json()) as TRes;
    return data;
}

/**
 * postFormToModal<TRes>
 * Purpose: send multipart/form-data to a Modal endpoint on the server.
 * This is used when we need to upload a file, like a .zip archive.
 * Generics:
 *  - TRes is the expected response JSON type. Use unknown at first if the shape is not final.
 * Parameters:
 *  - url: string. The destination endpoint URL, for example ENV_MODAL_PREPARE_URL.
 *  - form: FormData. A Web API FormData object that already contains fields and files.
 * Behavior:
 *  - We deliberately do NOT set the Content-Type header ourselves.
 *    fetch will set the correct multipart boundary for us.
 */
export async function postFormToModal<TRes = unknown>(url: string, form: FormData): Promise<TRes> {
    // Build headers. Only Authorization is needed if present.
    const headers: Record<string, string> = {};
    if (ENV_MODAL_SECRET_TOKEN && ENV_MODAL_SECRET_TOKEN.trim().length > 0) {
        headers.Authorization = `Bearer ${ENV_MODAL_SECRET_TOKEN}`;
    }

    // Send the multipart POST. Note we pass the FormData object as-is.
    const res = await fetch(url, {
        method: 'POST',
        headers,
        body: form
    });

    // Same error handling approach as JSON helper.
    if (!res.ok) {
        const text = await res.text().catch(() => '<no body>');
        throw new Error(`Modal multipart request failed with ${res.status}: ${text}`);
    }

    // Parse JSON and return.
    const data = (await res.json()) as TRes;
    return data;
}

// Small exported constants so other modules do not import env directly.
// Keeping these here centralizes anything Modal related for easy future swaps.
export const MODAL_PREPARE_URL = ENV_MODAL_PREPARE_URL!;
export const MODAL_SUMMARIZE_URL = ENV_MODAL_SUMMARIZE_URL!;