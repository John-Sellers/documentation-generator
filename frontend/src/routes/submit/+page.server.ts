// ─────────────────────────────────────────────────────────────────────────────
// PURPOSE
// - This file contains SvelteKit server "actions" that receive POSTs from forms
//   on the /submit page. We do *all* API calls to our Modal endpoints from here
//   (server-side), so secrets and tokens never touch the browser.
// - It implements two actions:
//     1) "prepare"   -> calls our Modal /prepare endpoint
//     2) "summarize" -> calls our Modal /summarize endpoint
// - It also has a "load" function that protects the page behind login.
// ─────────────────────────────────────────────────────────────────────────────

import { redirect } from '@sveltejs/kit';           // redirect() lets us send 303 responses cleanly
import type { Actions } from './$types';            // Type annotation for the actions object

// We import our server HTTP helpers and the two Modal URLs.
// These helpers live in src/lib/server/modalClient.ts and do a server-side fetch()
// with the right headers. This keeps all network calls on the server.
import {
    postJsonToModal,     // helper: POST JSON to an endpoint, parse JSON response, throw on non-2xx
    postFormToModal,     // helper: POST multipart/form-data (e.g., ZIP upload)
    MODAL_PREPARE_URL,   // string: your /prepare URL from .env (server-only)
    MODAL_SUMMARIZE_URL  // string: your /summarize URL from .env (server-only)
} from '$lib/server/modalClient';

// ─────────────────────────────────────────────────────────────────────────────
// ROUTE GUARD: ensure user is signed in before rendering /submit
// - SvelteKit calls "load" on GET requests. We read your Supabase session via
//   locals.safeGetSession (provided by your hooks). If no session, redirect.
// ─────────────────────────────────────────────────────────────────────────────
export const load = async ({ locals: { safeGetSession } }) => {
    const { session } = await safeGetSession(); // session is truthy when logged in
    if (!session) throw redirect(303, '/login'); // 303 = "See Other" (GET)
    return {}; // nothing special to send to the page right now
};

// ─────────────────────────────────────────────────────────────────────────────
// TYPES that mirror your Pydantic models so our JSON is correct.
// These are purely for TypeScript/editor help; they don’t run at runtime.
// ─────────────────────────────────────────────────────────────────────────────

// Exact JSON we send to /prepare in "application/json" mode
type PrepareJsonPayload = {
    input_type: 'github_repo' | 'github_repo_directory' | 'zipped_folder' | 'pasted_code';
    // GitHub fields:
    repo_url?: string;    // e.g. https://github.com/owner/repo
    repo_ref?: string;    // e.g. main | canary | a commit SHA
    subdir?: string;      // for github_repo_directory, e.g. "src/app"
    // ZIP by URL field:
    zip_url?: string;     // e.g. https://example.com/archive.zip
    // Pasted code:
    code_snippet?: string;
    // Optional filters/caps (your backend has defaults; we usually omit):
    include_globs?: string[] | null;
    exclude_globs?: string[] | null;
    max_files?: number | null;
    max_total_bytes?: number | null;
};

// What one "SectionSpec" looks like for /summarize
type SectionSpec = {
    id: string;                                   // key you want back in "sections"
    label?: string | null;                        // UI-only label
    type: 'short_text' | 'markdown' | 'list';     // controls the value shape
    required?: boolean | null;                    // hint for importance
    max_chars?: number | null;                    // only for short_text
    item_type?: string | null;                    // only for list (e.g., "string", "url")
    prompt_hint?: string | null;                  // extra instruction for this field
};

// Exact JSON we send to /summarize
type SummarizeJsonPayload = {
    source_id: string;           // REQUIRED (returned by /prepare)
    selected_paths: string[];    // REQUIRED (user-checked files)
    sections: SectionSpec[];     // REQUIRED (what we want back)
    constraints?: {
        audience?: string;
        tone?: string;
        reading_level?: string;
        max_tokens?: number;
    } | null;
    cleanup?: boolean | null;    // if true, backend deletes temp data after summarizing
};

// ─────────────────────────────────────────────────────────────────────────────
// UTIL: parse a GitHub "directory URL" like
//   https://github.com/<owner>/<repo>/tree/<ref>/<sub/dir/...>
// into { repo_url, repo_ref, subdir } for your backend.
// Returns null if the URL doesn’t match expected shape.
// ─────────────────────────────────────────────────────────────────────────────
function parseGithubDirectoryUrl(
    input: string
): null | { repo_url: string; repo_ref: string; subdir: string } {
    try {
        const url = new URL(input);                          // robust URL parsing
        if (url.hostname !== 'github.com') return null;      // only support github.com for now
        const parts = url.pathname.split('/').filter(Boolean); // ["owner","repo","tree","ref","sub","dir"]
        if (parts.length < 5) return null;
        const [owner, repo, treeLiteral, ref, ...rest] = parts;
        if (treeLiteral !== 'tree') return null;
        if (!owner || !repo || !ref || rest.length === 0) return null;
        const subdir = rest.join('/');                       // join remaining segments as subdir
        const repo_url = `https://github.com/${owner}/${repo}`;
        return { repo_url, repo_ref: ref, subdir };
    } catch {
        return null;                                         // invalid URL string
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// UTIL: derive a repo_ref (branch/tag/SHA) from a GitHub URL *without* any API.
// This only handles URLs that explicitly include a ref, e.g.:
//   - https://github.com/owner/repo/tree/<ref>/...
//   - https://github.com/owner/repo/blob/<ref>/...
// If there is no "/tree/<ref>" or "/blob/<ref>" segment, we return null.
// (For testing, this keeps things simple and requires the user to fill repo_ref.)
// ─────────────────────────────────────────────────────────────────────────────
function deriveRepoRefFromGithubUrlNoApi(repoUrl: string): string | null {
    try {
        const u = new URL(repoUrl);
        if (u.hostname !== 'github.com') return null;
        const parts = u.pathname.split('/').filter(Boolean); // ["owner","repo", maybe "tree","ref", ...]
        if (parts[2] === 'tree' && parts.length >= 4) return parts[3] || null;
        if (parts[2] === 'blob' && parts.length >= 4) return parts[3] || null;
        return null; // URL did not include a ref
    } catch {
        return null; // invalid URL
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// UTIL: normalize any thrown value to a safe string for the UI
// ─────────────────────────────────────────────────────────────────────────────
function toErrorMessage(err: unknown, fallback: string) {
    if (err && typeof err === 'object' && 'message' in err && typeof (err as any).message === 'string') {
        return String((err as any).message);
    }
    return fallback;
}

// ─────────────────────────────────────────────────────────────────────────────
// ACTIONS: the POST handlers that our forms call with action="?/prepare" and
//          action="?/summarize". The returned objects become the `form` prop
//          in +page.svelte (e.g., form.prepareResult, form.summarizeResult, form.error).
// ─────────────────────────────────────────────────────────────────────────────
export const actions: Actions = {
    // PREPARE: handles all four input types
    prepare: async ({ request }) => {
        try {
            const formData = await request.formData(); // parse urlencoded or multipart

            // small helpers to get typed values
            const getText = (name: string): string => {
                const v = formData.get(name);
                return typeof v === 'string' ? v : '';
            };
            const getFile = (name: string): File | null => {
                const v = formData.get(name);
                return v instanceof File ? v : null;
            };

            const input_type = getText('input_type') as PrepareJsonPayload['input_type'];
            if (!input_type) return { error: 'Missing input_type. Please choose a submission method.' };

            // ── pasted_code -> JSON body with code_snippet
            if (input_type === 'pasted_code') {
                const code_snippet = getText('code_snippet');
                if (!code_snippet.trim()) return { error: 'Please paste some code before submitting.' };
                const payload: PrepareJsonPayload = { input_type, code_snippet };
                const prepareResult = await postJsonToModal<PrepareJsonPayload, unknown>(MODAL_PREPARE_URL, payload);
                return { prepareResult };
            }

            // ── github_repo -> JSON body with repo_url + repo_ref
            if (input_type === 'github_repo') {
                const repo_url = getText('github_url');          // user input
                let repo_ref = getText('repo_ref');              // optional; try to derive if blank

                if (!repo_url.trim() || !repo_url.includes('github.com')) {
                    return { error: 'Please enter a valid GitHub repository URL.' };
                }

                if (!repo_ref.trim()) {
                    // Try to derive from URL segments only (no API calls)
                    repo_ref = deriveRepoRefFromGithubUrlNoApi(repo_url) || '';
                }

                if (!repo_ref.trim()) {
                    // We couldn’t derive; ask the user to provide it
                    return { error: 'Could not determine branch/tag/commit from the URL. Please fill repo_ref.' };
                }

                const payload: PrepareJsonPayload = { input_type, repo_url, repo_ref };
                const prepareResult = await postJsonToModal<PrepareJsonPayload, unknown>(MODAL_PREPARE_URL, payload);
                return { prepareResult };
            }

            // ── github_repo_directory -> JSON with repo_url + repo_ref + subdir
            if (input_type === 'github_repo_directory') {
                const directory_url = getText('directory_url'); // full URL including /tree/<ref>/<subdir...>
                let repo_ref = getText('repo_ref');             // optional; URL may include it

                if (!directory_url.trim() || !directory_url.includes('github.com')) {
                    return { error: 'Please enter a valid GitHub directory URL.' };
                }

                const parsed = parseGithubDirectoryUrl(directory_url);
                if (!parsed) {
                    return { error: 'Could not parse the directory URL. Expected: https://github.com/owner/repo/tree/<ref>/<subdir>' };
                }

                if (!repo_ref.trim()) repo_ref = parsed.repo_ref; // use the ref from the URL if user didn’t type one
                if (!repo_ref.trim()) {
                    return { error: 'Could not determine a branch/tag/commit. Please fill repo_ref.' };
                }

                const payload: PrepareJsonPayload = {
                    input_type,
                    repo_url: parsed.repo_url,
                    repo_ref,
                    subdir: parsed.subdir
                };
                const prepareResult = await postJsonToModal<PrepareJsonPayload, unknown>(MODAL_PREPARE_URL, payload);
                return { prepareResult };
            }

            // ── zipped_folder -> either multipart upload or JSON with zip_url
            if (input_type === 'zipped_folder') {
                const zipFile = getFile('zip_file'); // if the user uploaded a file
                const zip_url = getText('zip_url');  // OR a https link to a .zip

                if (zipFile) {
                    // multipart form (no JSON model on your backend for direct uploads)
                    const out = new FormData();
                    out.set('input_type', 'zipped_folder');
                    out.set('zip_file', zipFile, zipFile.name);
                    const prepareResult = await postFormToModal<unknown>(MODAL_PREPARE_URL, out);
                    return { prepareResult };
                }

                if (zip_url && zip_url.trim().length > 0) {
                    const payload: PrepareJsonPayload = { input_type, zip_url };
                    const prepareResult = await postJsonToModal<PrepareJsonPayload, unknown>(MODAL_PREPARE_URL, payload);
                    return { prepareResult };
                }

                return { error: 'Please upload a ZIP file or provide a https:// zip_url.' };
            }

            return { error: `Unsupported input_type: ${input_type}` };
        } catch (err: unknown) {
            return { error: toErrorMessage(err, 'Unknown server error while calling /prepare.') };
        }
    },

    // SUMMARIZE: takes source_id + selected_paths[] + a SectionSpec[] and calls /summarize
    summarize: async ({ request }) => {
        try {
            const formData = await request.formData();

            // REQUIRED: source_id (returned by /prepare)
            const source_id = String(formData.get('source_id') ?? '').trim();
            if (!source_id) return { error: 'Missing source_id from /prepare.' };

            // REQUIRED: at least one checkbox named "selected_paths"
            const selected_paths = formData.getAll('selected_paths')
                .map((v) => String(v))
                .filter((s) => s.length > 0);
            if (selected_paths.length === 0) {
                return { error: 'Please select at least one file to summarize.' };
            }

            // Define the output JSON shape we want back from the model.
            const sections: SectionSpec[] = [
                { id: 'title', label: 'Title', type: 'short_text', required: true, max_chars: 120, prompt_hint: 'One concise line a non‑technical stakeholder understands.' },
                { id: 'overview', label: 'Overview', type: 'markdown', required: true, prompt_hint: 'High-level, non‑technical summary: what the code does and why it matters.' },
                { id: 'key_points', label: 'Key points', type: 'list', required: true, item_type: 'string', prompt_hint: '3–7 short business‑friendly bullets.' },
                { id: 'references', label: 'References', type: 'list', required: false, item_type: 'url', prompt_hint: 'Relevant links (files, docs, repo paths).' }
            ];

            // Optional generation/style constraints.
            const constraints: SummarizeJsonPayload['constraints'] = {
                audience: 'business',
                tone: 'non_technical',
                reading_level: 'grade_8',
                max_tokens: 1200
            };

            // Build the exact body your backend expects.
            const payload: SummarizeJsonPayload = {
                source_id,
                selected_paths,
                sections,
                constraints,
                cleanup: true
            };

            // Server‑side POST to /summarize
            const summarizeResult = await postJsonToModal<SummarizeJsonPayload, unknown>(
                MODAL_SUMMARIZE_URL,
                payload
            );

            return { summarizeResult };
        } catch (err: unknown) {
            return { error: toErrorMessage(err, 'Unknown server error while calling /summarize.') };
        }
    }
};