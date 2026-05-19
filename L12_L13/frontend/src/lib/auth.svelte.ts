import { browser } from '$app/environment';
import { fetchCurrentUser, loginStaff, logoutStaff } from '$lib/api';
import type { LoginRequestPayload, User } from '$lib/types';

const sessionStorageKey = 'staff-session-token';

class AuthState {
	sessionToken = $state('');
	currentUser = $state<User | null>(null);
	isLoading = $state(false);
	isReady = $state(false);

	constructor() {
		if (browser) {
			this.sessionToken = window.localStorage.getItem(sessionStorageKey) ?? '';
		}
	}

	get isAuthenticated(): boolean {
		return this.sessionToken.length > 0 && this.currentUser !== null;
	}

	private syncSessionToken(): void {
		if (!browser) {
			return;
		}

		if (this.sessionToken) {
			window.localStorage.setItem(sessionStorageKey, this.sessionToken);
			return;
		}

		window.localStorage.removeItem(sessionStorageKey);
	}

	private setSession(sessionToken: string, user: User): void {
		this.sessionToken = sessionToken;
		this.currentUser = user;
		this.syncSessionToken();
	}

	clearSession(): void {
		this.sessionToken = '';
		this.currentUser = null;
		this.syncSessionToken();
	}

	async hydrate(): Promise<void> {
		if (this.isReady) {
			return;
		}

		this.isReady = true;
		if (!this.sessionToken) {
			return;
		}

		try {
			this.currentUser = await fetchCurrentUser(this.sessionToken);
		} catch {
			this.clearSession();
		}
	}

	async login(credentials: LoginRequestPayload): Promise<User> {
		this.isLoading = true;

		try {
			const response = await loginStaff(credentials);
			this.setSession(response.session_token, response.user);
			return response.user;
		} finally {
			this.isLoading = false;
		}
	}

	async logout(): Promise<void> {
		const token = this.sessionToken;
		this.clearSession();

		if (!token) {
			return;
		}

		try {
			await logoutStaff(token);
		} catch {
			// Logging out locally is enough for the UI even if the request fails.
		}
	}
}

export const authState = new AuthState();
