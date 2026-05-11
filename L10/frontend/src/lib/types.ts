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

export interface ReservationResponse {
	id: number;
	contact_name: string;
	contact_email: string;
	date: string;
	time: string;
	guest_count: number;
	special_requests: string | null;
}

export interface ApiValidationDetail {
	loc?: Array<string | number>;
	msg: string;
}
