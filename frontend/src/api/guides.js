import { getAuthToken } from './auth';

const API_BASE_URL = '/api';

function getHeaders(isJSON = true) {
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`,
    };
    if (isJSON) {
        headers['Content-Type'] = 'application/json';
    }
    return headers;
}

async function handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Request failed');
    }
    return data;
}

// Upload CSV (step 1 - just parse, don't generate yet)
export async function uploadGuide(file, companyWebsite = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_website', companyWebsite);

    const response = await fetch(`${API_BASE_URL}/guides/upload/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getAuthToken()}` },
        body: formData,
    });

    return handleResponse(response);
}

// Generate examples (step 2)
export async function generateGuideExamples(guideId) {
    const response = await fetch(`${API_BASE_URL}/guides/${guideId}/generate/`, {
        method: 'POST',
        headers: getHeaders(),
    });
    return handleResponse(response);
}

// Regenerate single cell
export async function regenerateCell(guideId, competency, level, feedback = '') {
    const response = await fetch(`${API_BASE_URL}/guides/${guideId}/regenerate-cell/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ competency, level, feedback }),
    });
    return handleResponse(response);
}

// Regenerate all cells
export async function regenerateAll(guideId, feedback = '') {
    const response = await fetch(`${API_BASE_URL}/guides/${guideId}/regenerate-all/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ feedback }),
    });
    return handleResponse(response);
}

// Get current guide
export async function getCurrentGuide() {
    const response = await fetch(`${API_BASE_URL}/guides/current/`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

// List all guides
export async function listGuides() {
    const response = await fetch(`${API_BASE_URL}/guides/`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

// Get single guide
export async function getGuide(guideId) {
    const response = await fetch(`${API_BASE_URL}/guides/${guideId}/`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

// Set as current version
export async function setCurrentVersion(guideId) {
    const response = await fetch(`${API_BASE_URL}/guides/${guideId}/set-current/`, {
        method: 'POST',
        headers: getHeaders(),
    });
    return handleResponse(response);
}
