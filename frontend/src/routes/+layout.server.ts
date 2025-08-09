// This runs only on the server for every page load.
// Its job is to fetch the current session once, then hand it to the client.
export const load = async ({ locals: { safeGetSession } }) => {
    // Ask our helper to read the auth cookie and verify it with Supabase.
    // If the user is not logged in, session and user will both be null.
    const { session, user } = await safeGetSession();

    // Return values become available in the browser as $page.data.session and $page.data.user.
    return {
        session,
        user
    };
};