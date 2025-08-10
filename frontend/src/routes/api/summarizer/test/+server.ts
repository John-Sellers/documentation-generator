// frontend/src/routes/api/summarizer/test/+server.ts

// Import this because the server route needs the helper that calls Modal.
import { summarizeProject } from '$lib/server/modal';

// Import this because SvelteKit expects a typed handler per HTTP verb.
import type { RequestHandler } from '@sveltejs/kit';

/**
 * GET /api/summarizer/test?path=/root/app
 *
 * Purpose:
 * - Call this request to verify the helper can reach Modal and parse a summary.
 * - Return summary length (not full text) to keep the payload small in dev.
 * - Accept an optional ?path=... query param; default to /root/app.
 */
export const GET: RequestHandler = async ({ url }) => {
    // Read this because callers may want to target a subdirectory; default matches your backend.
    const projectPath = url.searchParams.get('path') ?? '/root/app';

    try {
        // Call this because the helper abstracts URL, headers, timing, and parsing.
        const { summary } = await summarizeProject(
            { project_path: projectPath },
            {
                // Use this because a shorter timeout keeps the dev loop snappy.
                // Increase if your Modal function runs longer in your environment.
                timeoutMs: 45_000,
                retries: 1
            }
        );

        // Build this because returning the entire summary clutters the console/UI.
        const result = {
            ok: true,
            path: projectPath,
            summaryPreview: summary.slice(0, 160), // small peek for sanity
            summaryLength: summary.length
        };

        // Return this because JSON is easy to inspect in the browser and network tab.
        return new Response(JSON.stringify(result), {
            status: 200,
            headers: { 'content-type': 'application/json' }
        });
    } catch (err: any) {
        // Prepare this because clear server logs help diagnose failures quickly.
        console.error('Summarizer test error:', err?.message ?? err);

        // Return this because the client should see the failure in a structured way.
        const out = {
            ok: false,
            error: String(err?.message ?? err ?? 'Unknown error')
        };
        return new Response(JSON.stringify(out), {
            status: 502,
            headers: { 'content-type': 'application/json' }
        });
    }
};