// userApi.js (updated with better getOptimizedMap logging and timeout)

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

export const clearAllDatasets = async () => {
    try {
        const datasets = await getDatasets();
        
        for (const dataset of datasets) {
            if (dataset.id) {
                await $authHost.delete(`/api/jacobs/dataset/datasets/${dataset.id}`);
            }
        }
        
        return { success: true, message: 'All datasets cleared successfully' };
    } catch (err) {
        console.error('Error clearing datasets:', err);
        throw err;
    }
};

export const getClient = async (client_number) => {
    try {
        console.log('Fetching client with number:', client_number); // For debugging
        const { data } = await $authHost.get(`/api/jacobs/dataset/clients/${client_number}`);
        console.log('Client data:', data); // For debugging
        return data;
    } catch (err) {
        // Улучшенный лог для 422
        if (err.response?.status === 422) {
            console.error('Validation error details:', err.response.data.detail);
        } else {
            console.error('API Error Details for getClient:', err.response?.data || err.message);
        }
        throw err;
    }
};

export const refreshToken = async () => {
    const storedRefreshToken = localStorage.getItem('refresh_token');

    if (!storedRefreshToken) {
        throw new Error('No refresh token available');
    }

    try {
        const { data } = await $host.post(
            '/api/jacobs/auth/refresh',
            null,
            {
                headers: {
                    Authorization: `Bearer ${storedRefreshToken}`,
                },
            },
        );

        const newAccessToken = data?.access_token;
        const newRefreshToken = data?.refresh_token;

        if (!newAccessToken || !newRefreshToken) {
            throw new Error('Invalid refresh response');
        }

        localStorage.setItem('token', newAccessToken);
        localStorage.setItem('refresh_token', newRefreshToken);

        return newAccessToken;
    } catch (err) {
        console.error('Refresh token failed:', err);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        throw err;
    }
};

export const updateMeeting = async (clientNumber, successful) => {
    try {
        const { data } = await $authHost.post(`/api/jacobs/dataset/clients/${clientNumber}/meeting`, { 
            meeting_successful: successful 
        });
        console.log('Meeting update response:', data); // For debugging
        return data;
    } catch (err) {
        console.error('API Error Details for updateMeeting:', err.response?.data || err.message);
        throw err;
    }
};

export const getOptimizedMap = async () => {
    try {
        console.log('Starting getOptimizedMap request... Token:', localStorage.getItem('token') ? 'Present' : 'Missing');  // Лог auth
        const { data } = await $authHost.post('/api/jacobs/routing/optimize/map', {}, {
            timeout: 20000,  // 20с таймаут для 10с + буфер
        });
        console.log('Map HTML received (length):', data.length);  // Лог размера HTML
        if (!data || typeof data !== 'string' || data.trim() === '') {
            throw new Error('Пустой HTML от API');
        }
        return data;  // HTML-строка
    } catch (err) {
        if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
            throw new Error('Таймаут: Генерация карты заняла >20с. Попробуйте снова.');
        }
        if (err.response?.status === 401) {
            console.log('401 - Token invalid, trying refresh...');
            await refreshToken();  // Авто-обновление токена
            // Retry once
            const { data } = await $authHost.post('/api/jacobs/routing/optimize/map', {}, { timeout: 20000 });
            return data;
        }
        console.error('Full API Error for getOptimizedMap:', {
            status: err.response?.status,
            data: err.response?.data,
            message: err.message
        });
        throw err;
    }
};
