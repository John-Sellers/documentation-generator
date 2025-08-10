// Import this because the helper must access server-only env variables safely.
// $env/static/private ensures these never ship to the browser bundle.
import { MODAL_SUMMARIZER_URL, MODAL_SUMMARIZER_TOKEN } from '$env/static/private';

// Import this because the code will use AbortController for request timeouts in Node.
import { setTimeout as nodeSleep } from 'node:timers/promises';

// -----------------------------
// Types
// -----------------------------

// Export this because callers should pass a concrete project path to summarize.
export type SummarizeRequest = {
    // Use this because the backend expects a filesystem path inside the Modal container.
    // The default in your FastAPI code is "/root/app"; callers may override if needed.
    project_path: string;
};

// Export this because the helper will resolve with a strict shape after a successful call.
export type SummarizeResponse = {
    // Use this because the API returns a single string under "summary".
    summary: string;
};

// Export this because upstream code may want to tweak behaviors (e.g., shorter timeout during tests).
export type SummarizeOptions = {
    // Use this because long LLM jobs may run for many seconds; default keeps dev responsive.
    timeoutMs?: number;   // default 60_000
    // Use this because transient network hiccups happen; a tiny retry can smooth them out.
    retries?: number;     // default 1 (i.e., up to 2 total attempts)
    // Use this because the caller may want to pass a custom fetch (usually unnecessary).
    fetchImpl?: typeof fetch;
};

// -----------------------------
// Helper
// -----------------------------

// Export this because other server code (actions, endpoints) should call a single, well-typed function.
export async function summarizeProject(
    body: SummarizeRequest,
    opts: SummarizeOptions = {}
): Promise<SummarizeResponse> {
    // Compute this because sensible defaults reduce call-site repetition.
    const timeoutMs = opts.timeoutMs ?? 60_000; // 60s default
    const retries = Math.max(0, Math.min(opts.retries ?? 1, 3)); // clamp between 0 and 3
    const fetchImpl = opts.fetchImpl ?? fetch;

    // Validate this because failing fast with clear messages saves time.
    if (!MODAL_SUMMARIZER_URL) {
        throw new Error('Summarizer URL is missing. Did you set MODAL_SUMMARIZER_URL in .env?');
    }
    if (!MODAL_SUMMARIZER_TOKEN) {
        throw new Error('Summarizer token is missing. Did you set MODAL_SUMMARIZER_TOKEN in .env?');
    }
    if (!body?.project_path || typeof body.project_path !== 'string') {
        throw new Error('Invalid request: "project_path" must be a non-empty string.');
    }

    // Prepare this because Modal expects JSON with the Authorization: Bearer header.
    const payload = JSON.stringify({ project_path: body.project_path });

    // Define this because a small retry loop can mask brief network blips.
    let lastError: unknown;
    for (let attempt = 0; attempt <= retries; attempt++) {
        // Create this because AbortController enforces an upper bound on request time.
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        try {
            // Call this request because it hits your Modal FastAPI function over HTTPS.
            const res = await fetchImpl(MODAL_SUMMARIZER_URL, {
                method: 'POST',
                headers: {
                    'content-type': 'application/json',
                    authorization: `Bearer ${MODAL_SUMMARIZER_TOKEN}`
                },
                body: payload,
                signal: controller.signal
            });

            // Clear this because the request has settled (avoid leaking timers).
            clearTimeout(timer);

            // Check this because non-2xx should surface a helpful error early.
            if (!res.ok) {
                // Attempt this because response text often carries the root cause from FastAPI.
                const text = await safeReadText(res);
                throw new Error(`Modal call failed: ${res.status} ${res.statusText} – ${text ?? '(no body)'}`);
            }

            // Parse this because the API returns JSON (e.g., { "summary": "..." }).
            const data = (await res.json()) as unknown;

            // Validate this because the frontend expects a strict `{ summary: string }`.
            const summary = (data as any)?.summary;
            if (typeof summary !== 'string' || summary.length === 0) {
                throw new Error('Modal response missing "summary" string.');
            }

            // Return this because the response shape matches the contract.
            return { summary };
        } catch (err) {
            // Clear this because the catch block may fire before clearing above.
            clearTimeout(timer);
            lastError = err;

            // Decide this because only retry on network/timeout; not on 4xx from server.
            const retryable =
                isAbortError(err) ||
                isLikeNetworkError(err) ||
                // Some hosting environments throw generic TypeErrors on fetch failures.
                err instanceof TypeError;

            // Sleep this because a tiny backoff helps transient issues.
            if (attempt < retries && retryable) {
                await nodeSleep(250 * (attempt + 1));
                continue;
            }

            // Throw this because either retries are exhausted or the error is not retryable.
            throw err;
        }
    }

    // Throw this because control should never reach here; loop either returns or throws earlier.
    throw lastError instanceof Error ? lastError : new Error('Unknown error calling Modal summarizer');
}

// -----------------------------
// Small internals
// -----------------------------

// Define this because some environments produce DOMException-like abort errors without a shared class.
function isAbortError(err: unknown): boolean {
    return (
        !!err &&
        typeof err === 'object' &&
        ('name' in err ? (err as any).name === 'AbortError' : false)
    );
}

// Define this because node-fetch and undici may surface different network failure messages.
function isLikeNetworkError(err: unknown): boolean {
    if (!err || typeof err !== 'object') return false;
    const msg = String((err as any).message ?? '').toLowerCase();
    return (
        msg.includes('network') ||
        msg.includes('fetch') ||
        msg.includes('failed to') ||
        msg.includes('socket') ||
        msg.includes('timeout') ||
        msg.includes('aborted') ||
        msg.includes('offline')
    );
}

// Define this because reading response.text() can itself fail on empty/consumed bodies.
async function safeReadText(res: Response): Promise<string | null> {
    try {
        const t = await res.text();
        return t || null;
    } catch {
        return null;
    }
}