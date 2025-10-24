import { $authHost, $host } from ".";
import { jwtDecode } from "jwt-decode";

export const Registration = async (email, password) => {
    const {data} = await $host.post('/api/jacobs/auth/register', {email, password})
    localStorage.setItem('token', data.token)
    return jwtDecode(data.token)
}

export const Login = async (email, password) => {
    const {data} = await $host.post('/api/jacobs/auth/login', {email, password})
    localStorage.setItem('token', data.token)
    return jwtDecode(data.token)
}

export const check = async () => {
    const {data} = await $authHost.get('/api/user/auth')
    localStorage.setItem('token', data.token)
    return jwtDecode(data.token)
}