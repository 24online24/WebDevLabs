import { apiBasePath, sessionHeaderName } from '$lib/config';
import type {
	ApiErrorResponse,
	ApiValidationDetail,
	LoginRequestPayload,
	MenuItem,
	MenuItemPayload,
	ReservationCreatePayload,
	ReservationFilters,
	ReservationResponse,
	ReservationUpdatePayload,
	StaffUserCreatePayload,
	StaffUserUpdatePayload,
	SessionResponse,
	User
} from '$lib/types';

type ApiRequestOptions = RequestInit & {
	sessionToken?: string;
};

export class ApiError extends Error {
	status: number;
	detail?: string | ApiValidationDetail[];

	constructor(status: number, detail?: string | ApiValidationDetail[]) {
		super(typeof detail === 'string' ? detail : 'API request failed.');
		this.name = 'ApiError';
		this.status = status;
		this.detail = detail;
	}
}

function isApiErrorResponse(data: unknown): data is ApiErrorResponse {
	return typeof data === 'object' && data !== null && 'detail' in data;
}

async function readResponseData(response: Response): Promise<unknown> {
	const contentType = response.headers.get('content-type') ?? '';
	if (!contentType.includes('application/json')) {
		return null;
	}

	return await response.json();
}

function buildHeaders(headersInit: HeadersInit | undefined, sessionToken?: string): Headers {
	const headers = new Headers(headersInit);
	if (sessionToken) {
		headers.set(sessionHeaderName, sessionToken);
	}

	return headers;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
	const { sessionToken, headers: headersInit, ...requestInit } = options;
	const response = await fetch(`${apiBasePath}${path}`, {
		...requestInit,
		headers: buildHeaders(headersInit, sessionToken)
	});
	const data = await readResponseData(response);

	if (!response.ok) {
		const detail = isApiErrorResponse(data) ? data.detail : undefined;
		throw new ApiError(response.status, detail);
	}

	return data as T;
}

export function formatApiValidationDetail(detail: ApiValidationDetail): string {
	const fieldName = detail.loc?.[detail.loc.length - 1];
	if (!fieldName) {
		return detail.msg;
	}

	const label = String(fieldName).replaceAll('_', ' ');
	return `${label}: ${detail.msg}`;
}

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
	if (error instanceof ApiError) {
		if (Array.isArray(error.detail)) {
			return error.detail.map(formatApiValidationDetail).join(' ');
		}

		if (typeof error.detail === 'string') {
			return error.detail;
		}
	}

	return fallbackMessage;
}

export function loginStaff(payload: LoginRequestPayload): Promise<SessionResponse> {
	return apiRequest<SessionResponse>('/auth/login', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}

export function fetchMenuItems(category?: string): Promise<MenuItem[]> {
	const searchParams = new URLSearchParams();
	if (category) {
		searchParams.set('category', category);
	}

	const queryString = searchParams.toString();
	const path = queryString ? `/menu?${queryString}` : '/menu';
	return apiRequest<MenuItem[]>(path);
}

export function createReservation(payload: ReservationCreatePayload): Promise<ReservationResponse> {
	return apiRequest<ReservationResponse>('/reservations', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}

export function createMenuItem(sessionToken: string, payload: MenuItemPayload): Promise<MenuItem> {
	return apiRequest<MenuItem>('/menu', {
		method: 'POST',
		sessionToken,
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}

export function updateMenuItem(
	sessionToken: string,
	menuItemId: number,
	payload: MenuItemPayload
): Promise<MenuItem> {
	return apiRequest<MenuItem>(`/menu/${menuItemId}`, {
		method: 'PUT',
		sessionToken,
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}

export async function deleteMenuItem(sessionToken: string, menuItemId: number): Promise<void> {
	await apiRequest<{ status: string }>(`/menu/${menuItemId}`, {
		method: 'DELETE',
		sessionToken
	});
}

export function fetchStaffUsers(sessionToken: string): Promise<User[]> {
	return apiRequest<User[]>('/staff/users', { sessionToken });
}

export function createStaffUser(
	sessionToken: string,
	payload: StaffUserCreatePayload
): Promise<User> {
	return apiRequest<User>('/staff/users', {
		method: 'POST',
		sessionToken,
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}

export function updateStaffUser(
	sessionToken: string,
	userId: number,
	payload: StaffUserUpdatePayload
): Promise<User> {
	return apiRequest<User>(`/staff/users/${userId}`, {
		method: 'PATCH',
		sessionToken,
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}

export function fetchCurrentUser(sessionToken: string): Promise<User> {
	return apiRequest<User>('/auth/me', { sessionToken });
}

export async function logoutStaff(sessionToken: string): Promise<void> {
	await apiRequest<{ status: string }>('/auth/logout', {
		method: 'POST',
		sessionToken
	});
}

export function fetchReservations(
	sessionToken: string,
	filters: ReservationFilters = {}
): Promise<ReservationResponse[]> {
	const searchParams = new URLSearchParams();

	if (filters.date) {
		searchParams.set('date', filters.date);
	}

	if (filters.status) {
		searchParams.set('status', filters.status);
	}

	const queryString = searchParams.toString();
	const path = queryString ? `/reservations?${queryString}` : '/reservations';

	return apiRequest<ReservationResponse[]>(path, { sessionToken });
}

export function updateReservation(
	sessionToken: string,
	reservationId: number,
	payload: ReservationUpdatePayload
): Promise<ReservationResponse> {
	return apiRequest<ReservationResponse>(`/reservations/${reservationId}`, {
		method: 'PATCH',
		sessionToken,
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
}
