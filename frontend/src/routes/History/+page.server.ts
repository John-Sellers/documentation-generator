// [1] The server load receives the event. We only use locals here.
export const load = async ({ locals: { safeGetSession } }) => {
    // [2] Ask our helper for the current session and user.
    const { session, user } = await safeGetSession();

    // [3] Return simple data to the page. hasSession is true if a session exists.
    return {
        hasSession: Boolean(session),
        email: user ? user.email : null
    };
};
