import { useNavigate } from 'react-router-dom'
import cl from '../styles/registerpage.module.css'
import { AUTH_ROUTE } from '../configs/consts'

const RegisterPage = () => {
    const navigate = useNavigate()

    return (
        <div className={cl.container}>
            <h1 className={cl.title}>Создать аккаунт</h1>
            <form className={cl.form}>
                <input 
                    type="email" 
                    placeholder="Email" 
                    className={cl.input} 
                />
                <input 
                    type="password" 
                    placeholder="Пароль" 
                    className={cl.input} 
                />
                <input 
                    type="password" 
                    placeholder="Подтвердите пароль" 
                    className={cl.input} 
                />
                <button type="submit" className={cl.button}>
                    Создать аккаунт
                </button>
            </form>
            <p className={cl.link}>
                Уже есть аккаунт? <a onClick={() => navigate(AUTH_ROUTE)} >Войти</a>
            </p>
        </div>
    )
}

export default RegisterPage