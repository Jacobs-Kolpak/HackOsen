import { useState, useContext, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import cl from '../styles/authpage.module.css'
import { REGISTER_ROUTE, DASHBOARD_ROUTE } from '../configs/consts'
import LogoReg from '../assets/LogoReg.svg'
import email from '../assets/email.svg'
import password from '../assets/password.svg'
import eye from '../assets/eye.svg'
import loginIcon from '../assets/login.svg'
import { Login } from '../api/userApi'
import { UserContext } from '../context/UserContext'

const AuthPage = () => {
    const navigate = useNavigate()
    const { login } = useContext(UserContext)

    const [emailValue, setEmailValue] = useState('')
    const [passwordValue, setPasswordValue] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [showToast, setShowToast] = useState(false)

    const togglePasswordVisibility = () => setShowPassword(!showPassword)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const userData = await Login(emailValue, passwordValue)
            login(userData)
            navigate(DASHBOARD_ROUTE)
        } catch (err) {
            console.error('Ошибка авторизации:', err)
            setError('Неверный email или пароль.')
            setShowToast(true)
        } finally {
            setLoading(false)
        }
    }

    // Автоматическое скрытие уведомления через 3 секунды
    useEffect(() => {
        if (showToast) {
            const timer = setTimeout(() => setShowToast(false), 3000)
            return () => clearTimeout(timer)
        }
    }, [showToast])

    return (
        <div className={cl.container}>
            {/* Всплывающее уведомление */}
            {showToast && (
                <div className={cl.toast}>
                    {error}
                </div>
            )}

            <img src={LogoReg} className={cl.img} alt="Logo" />
            <div className={cl.formMain}>
                <h1 className={cl.title}>С возвращением!</h1>
                <p className={cl.grayText}>Войдите, чтобы продолжить работу</p>

                <form className={cl.form} onSubmit={handleSubmit}>
                    <div className={cl.email}>
                        <img src={email} className={cl.miniImg} alt="email" />
                        <p>Email</p>
                    </div>
                    <input
                        type="email"
                        placeholder="ivanov@example.com"
                        className={cl.input}
                        value={emailValue}
                        onChange={(e) => setEmailValue(e.target.value)}
                        required
                    />

                    <div className={cl.password}>
                        <img src={password} className={cl.miniImg} alt="password" />
                        <p>Пароль</p>
                    </div>

                    <div className={cl.inputContainer}>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Пароль"
                            className={cl.inputPassword}
                            value={passwordValue}
                            onChange={(e) => setPasswordValue(e.target.value)}
                            required
                        />
                        <button
                            type="button"
                            onClick={togglePasswordVisibility}
                            className={cl.toggleButton}
                        >
                            <img src={eye} alt="toggle password" />
                        </button>
                    </div>

                    <button type="submit" className={cl.button} disabled={loading}>
                        <img src={loginIcon} className={cl.miniImg} alt="login" />
                        {loading ? 'Вход...' : 'Войти в систему'}
                    </button>
                </form>

                <p className={cl.link}>
                    Нет аккаунта?{' '}
                    <a onClick={() => navigate(REGISTER_ROUTE)}>Зарегистрироваться</a>
                </p>
            </div>
        </div>
    )
}

export default AuthPage
