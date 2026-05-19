import { env } from '$env/dynamic/public';

export const apiBasePath = env.PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api';
export const sessionHeaderName = 'X-Session-Token';
