import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import cl from '../styles/authpage.module.css'
import { REGISTER_ROUTE } from '../configs/consts'
import LogoReg from '../assets/LogoReg.svg'
import email from '../assets/email.svg'
import password from '../assets/password.svg'
import eye from '../assets/eye.svg'
import login from '../assets/login.svg'

const AuthPage = () => {
    const navigate = useNavigate()
    const [showPassword, setShowPassword] = useState(false)

    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword)
    }

    return (
        <div className={cl.container}>
            <img src={LogoReg} className={cl.img} />
            <div className={cl.formMain}>
                <h1 className={cl.title}>С возвращением!</h1>
                <p className={cl.grayText}>Войдите, чтобы продолжить работу</p>
                <form className={cl.form}>
                    <div className={cl.email}>
                        <img src={email} className={cl.miniImg} />
                        <p>Email</p>
                    </div>
                    <input 
                        type="email" 
                        placeholder="ivanov@example.com" 
                        className={cl.input} 
                    />
                    <div className={cl.password}>
                        <img src={password} className={cl.miniImg} />
                        <p>Пароль</p>
                    </div>
                    <div className={cl.inputContainer}>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Пароль"
                            className={cl.inputPassword}
                        />
                        <button
                            type="button"
                            onClick={togglePasswordVisibility}
                            className={cl.toggleButton}
                        >
                            <img src={eye} />
                        </button>
                    </div>
                    <button type="submit" className={cl.button}>
                        <img src={login} className={cl.miniImg} />
                        Войти в систему
                    </button>
                </form>
                <p className={cl.link}>
                    Нет аккаунта? <a onClick={() => navigate(REGISTER_ROUTE)} >Зарегистрироваться</a>
                </p>
            </div>
        </div>
    )
}

export default AuthPage