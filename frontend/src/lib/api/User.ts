export type CurrentUser = { id: number; name: string } | null;

export const User = {
    async me(): Promise<CurrentUser> {
        return Promise.resolve({ id: 1, name: "John" }); // fake logged-in user
    }
};