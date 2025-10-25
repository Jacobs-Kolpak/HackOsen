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