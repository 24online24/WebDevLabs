import { apiBasePath, sessionHeaderName } from '$lib/config';
import type {
	ApiErrorResponse,
	ApiValidationDetail,
	LoginRequestPayload,
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

export function fetchCurrentUser(sessionToken: string): Promise<User> {
	return apiRequest<User>('/auth/me', { sessionToken });
}

export async function logoutStaff(sessionToken: string): Promise<void> {
	await apiRequest<{ status: string }>('/auth/logout', {
		method: 'POST',
		sessionToken
	});
}
