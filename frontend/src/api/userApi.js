// userApi.js
import { $authHost, $host } from ".";
import { jwtDecode } from "jwt-decode";

export const Registration = async (first_name, last_name, email, password) => {
    const { data } = await $host.post('/api/jacobs/auth/register', {
        first_name,
        last_name,
        email,
        password
    })
    return data
}

export const Login = async (email, password) => {
    const { data } = await $host.post('/api/jacobs/auth/login', { email, password })
    console.log('Ответ сервера при логине:', data)

    const token = data.access_token

    if (!token || typeof token !== 'string') {
        throw new Error('Invalid token received from server')
    }
    localStorage.setItem('token', token)
    localStorage.setItem('refresh_token', data.refresh_token)

    const decoded = jwtDecode(token)

    return decoded
}

export const Profile = async () => {
    const { data } = await $authHost.get('/api/jacobs/auth/me')
    return data.user
}

export const getOptimizedRoute = async () => {
    try {
        const { data } = await $authHost.post('/api/jacobs/routing/optimize');
        if (!data.success) {
            throw new Error(data.message || 'Ошибка оптимизации маршрута');
        }
        // Преобразуем route_points в формат, ожидаемый компонентом
        const points = data.route_points.map((point) => ({
            id: point.object_number,
            lat: point.latitude,
            lng: point.longitude,
            address: point.address,
        }));
        return points;
    } catch (err) {
        console.error('API Error Details:', err.response?.data || err.message); // Добавьте это для логов
        throw err; // Перебросьте ошибку для обработки в компоненте
    }
};

export const uploadDataset = async (file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        const { data } = await $authHost.post('/api/jacobs/dataset/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return data;
    } catch (err) {
        console.error('API Error Details:', err.response?.data || err.message);
        throw err;
    }
};

export const getDatasets = async () => {
    try {
        const { data } = await $authHost.get('/api/jacobs/dataset/datasets');
        return data.datasets || data || [];
    } catch (err) {
        console.error('API Error Details:', err.response?.data || err.message);
        throw err;
    }
};

export const optimizeRoute = async () => {
    try {
        const { data } = await $authHost.post('/api/jacobs/routing/optimize');
        console.log('Данные с сервера при оптимизации:', data); // Вывод значений в консоль
        if (!data.success) {
            throw new Error(data.message || 'Ошибка оптимизации маршрута');
        }
        return data;
    } catch (err) {
        console.error('API Error Details:', err.response?.data || err.message);
        throw err;
    }
};




export const refreshToken = async () => {
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        const { data } = await $host.post('/api/jacobs/auth/refresh', { refresh_token: refreshToken });
        const newToken = data.access_token;
        if (!newToken) {
            throw new Error('Invalid refresh response');
        }
        localStorage.setItem('token', newToken);
        return newToken;
    } catch (err) {
        console.error('Refresh token failed:', err);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        throw err;
    }
};