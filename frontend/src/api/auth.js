const API_BASE_URL = '/api';

export async function login(username, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || 'Login failed');
    }

    return data;
}

export function getAuthToken() {
    return localStorage.getItem('token');
}

export function setAuthToken(token) {
    localStorage.setItem('token', token);
}

export function removeAuthToken() {
    localStorage.removeItem('token');
}

export function isAuthenticated() {
    return !!getAuthToken();
}
