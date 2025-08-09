// We use SvelteKit's redirect helper to send guests to the login page
import { redirect } from '@sveltejs/kit';

export const load = async ({ locals: { safeGetSession } }) => {
    // Ask our helper, which reads the Supabase cookie and validates it
    const { session } = await safeGetSession();

    // If there is no session, the user is not logged in
    if (!session) {
        // 303 tells the browser to go to this other page using GET
        throw redirect(303, '/login');
    }

    // If there is a session, allow the page to render
    // You can return data for the page here if needed
    return {};
};