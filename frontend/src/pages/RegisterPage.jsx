import { useState, useContext, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import cl from '../styles/registerpage.module.css'
import { AUTH_ROUTE, DASHBOARD_ROUTE } from '../configs/consts'
import { Registration, Login } from '../api/userApi'
import { UserContext } from '../context/UserContext'
import LogoReg from '../assets/LogoReg.svg'
import userIcon from '../assets/user.svg'
import emailIcon from '../assets/email.svg'
import passwordIcon from '../assets/password.svg'
import confirmPasswordIcon from '../assets/password2.svg'
import eye from '../assets/eye.svg'

const RegisterPage = () => {
    const navigate = useNavigate()
    const { registration } = useContext(UserContext)

    const [showPassword, setShowPassword] = useState(false)
    const [firstName, setFirstName] = useState('')
    const [lastName, setLastName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [showToast, setShowToast] = useState(false)

    const togglePasswordVisibility = () => setShowPassword(!showPassword)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setShowToast(false)

        if (!firstName || !lastName || !email || !password || !confirmPassword) {
            setError('Заполните все поля')
            setShowToast(true)
            return
        }

        if (password !== confirmPassword) {
            setError('Пароли не совпадают')
            setShowToast(true)
            return
        }

        try {
            setLoading(true)
            await Registration(firstName, lastName, email, password)
            const userData = await Login(email, password)
            registration(userData)
            navigate(DASHBOARD_ROUTE)
        } catch (err) {
            console.error('Ошибка регистрации:', err)
            setError('Ошибка при регистрации. Проверьте данные.')
            setShowToast(true)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (showToast) {
            const timer = setTimeout(() => setShowToast(false), 3000)
            return () => clearTimeout(timer)
        }
    }, [showToast])

    return (
        <div className={cl.container}>
            {showToast && <div className={cl.toast}>{error}</div>}

            <img src={LogoReg} className={cl.img} alt="logo" />
            <div className={cl.formMain}>
                <h1 className={cl.title}>Создать аккаунт</h1>
                <p className={cl.grayText}>Заполните форму для регистрации</p>

                <form className={cl.form} onSubmit={handleSubmit}>
                    <div className={cl.nameSurname}>
                        <div className={cl.name}>
                            <div className={cl.textImg}>
                                <img src={userIcon} className={cl.miniImg} />
                                <p>Имя</p>
                            </div>
                            <input
                                type="text"
                                placeholder="Иван"
                                className={cl.inputName}
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                            />
                        </div>
                        <div className={cl.surname}>
                            <div className={cl.textImg}>
                                <img src={userIcon} className={cl.miniImg} />
                                <p>Фамилия</p>
                            </div>
                            <input
                                type="text"
                                placeholder="Иванов"
                                className={cl.inputSurname}
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className={cl.email}>
                        <img src={emailIcon} className={cl.miniImg} />
                        <p>Email</p>
                    </div>
                    <input
                        type="email"
                        placeholder="ivanov@example.com"
                        className={cl.input}
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <div className={cl.password}>
                        <img src={passwordIcon} className={cl.miniImg} />
                        <p>Пароль</p>
                    </div>
                    <div className={cl.inputContainer}>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Пароль"
                            className={cl.inputPassword}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        <button
                            type="button"
                            onClick={togglePasswordVisibility}
                            className={cl.toggleButton}
                        >
                            <img src={eye} alt="toggle password" />
                        </button>
                    </div>

                    <div className={cl.confirmPassword}>
                        <img src={confirmPasswordIcon} className={cl.miniImg} />
                        <p>Подтверждение пароля</p>
                    </div>
                    <div className={cl.inputContainer}>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Подтвердите пароль"
                            className={cl.inputPassword}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                        <button
                            type="button"
                            onClick={togglePasswordVisibility}
                            className={cl.toggleButton}
                        >
                            <img src={eye} alt="toggle password" />
                        </button>
                    </div>

                    <button
                        type="submit"
                        className={cl.button}
                        disabled={loading}
                    >
                        {loading ? 'Создание...' : 'Создать аккаунт'}
                    </button>
                </form>

                <p className={cl.link}>
                    Уже есть аккаунт?{' '}
                    <a onClick={() => navigate(AUTH_ROUTE)}>Войти</a>
                </p>
            </div>
        </div>
    )
}

export default RegisterPage