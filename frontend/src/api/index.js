// src/api/index.js

import axios from 'axios';
import { refreshToken } from './userApi.js'; // Import refreshToken from userApi.js

const API_URL = 'http://localhost:8000';

export const $host = axios.create({
    baseURL: API_URL
});

export const $authHost = axios.create({
    baseURL: API_URL
});

const authInterceptor = config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`; // Capital 'A' for standard casing
        console.log('Token added to headers:', token.substring(0, 20) + '...'); // Debug log (remove in prod)
    } else {
        console.warn('No token found in localStorage'); // Debug log
    }
    return config;
};

$authHost.interceptors.request.use(authInterceptor);

// Response interceptor: Handle 401/403 errors with token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });

    failedQueue = [];
};

$authHost.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        const status = error.response?.status;

        // Treat both 401 and 403 as auth errors
        if ((status === 401 || status === 403) && !originalRequest._retry) {
            if (isRefreshing) {
                // If refresh is in progress, queue the request
                return new Promise(function (resolve, reject) {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        originalRequest.headers.Authorization = `Bearer ${token}`;
                        return $authHost(originalRequest);
                    })
                    .catch((err) => {
                        return Promise.reject(err);
                    });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Attempt to refresh token
                const newToken = await refreshToken();
                $authHost.defaults.headers.Authorization = `Bearer ${newToken}`;
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                processQueue(null, newToken);

                // Retry the original request
                return $authHost(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError, null);
                // Clear invalid tokens on refresh failure
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                console.error('Auth refresh failed, redirecting to login');
                // Let the component handle redirect (your existing 401/403 logic in RoutesPage)
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        // For other errors, just reject
        return Promise.reject(error);
    }
);