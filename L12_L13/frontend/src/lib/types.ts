export interface MenuItem {
	id: number;
	name: string;
	category: string;
	price: number;
	description: string;
	image: string;
	alt: string;
	isFeatured: boolean;
}

export interface MenuItemPayload {
	name: string;
	category: string;
	price: number;
	description: string;
	image: string;
	alt: string;
	isFeatured: boolean;
}

export interface ReservationResponse {
	id: number;
	contact_name: string;
	contact_email: string;
	date: string;
	time: string;
	guest_count: number;
	special_requests: string | null;
	status: ReservationStatus;
	internal_notes: string | null;
	created_at: string;
	updated_at: string;
	updated_by_id: number | null;
}

export interface ReservationCreatePayload {
	contact_name: string;
	contact_email: string;
	date: string;
	time: string;
	guest_count: number;
	special_requests: string | null;
}

export type ReservationStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled';

export interface ReservationFilters {
	date?: string;
	status?: ReservationStatus;
}

export interface ReservationUpdatePayload {
	contact_name?: string;
	contact_email?: string;
	date?: string;
	time?: string;
	guest_count?: number;
	special_requests?: string | null;
	status?: ReservationStatus;
	internal_notes?: string | null;
}

export interface ApiValidationDetail {
	loc?: Array<string | number>;
	msg: string;
}

export type UserRole = 'admin' | 'manager';

export interface User {
	id: number;
	email: string;
	display_name: string;
	role: UserRole;
	is_active: boolean;
	created_at: string;
}

export interface StaffUserCreatePayload {
	email: string;
	display_name: string;
	password: string;
	role: UserRole;
}

export interface StaffUserUpdatePayload {
	display_name?: string;
	role?: UserRole;
	is_active?: boolean;
}

export interface LoginRequestPayload {
	email: string;
	password: string;
}

export interface SessionResponse {
	session_token: string;
	user: User;
}

export interface ApiErrorResponse {
	detail?: string | ApiValidationDetail[];
}
