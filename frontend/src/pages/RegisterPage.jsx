import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import cl from '../styles/registerpage.module.css'
import { AUTH_ROUTE } from '../configs/consts'
import LogoReg from '../assets/LogoReg.svg'
import user from '../assets/user.svg'
import email from '../assets/email.svg'
import password from '../assets/password.svg'
import confirmPassword from '../assets/password2.svg'
import eye from '../assets/eye.svg'

const RegisterPage = () => {
    const navigate = useNavigate()
    const [showPassword, setShowPassword] = useState(false)

    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword)
    }

    return (
        <div className={cl.container}>
            <img src={LogoReg} className={cl.img} />
            <div className={cl.formMain}>
                <h1 className={cl.title}>Создать аккаунт</h1>
                <p className={cl.grayText}>Заполните форму для регистрации</p>
                <form className={cl.form}>
                    <div className={cl.nameSurname}>
                        <div className={cl.name}>
                            <div className={cl.textImg}>
                                <img src={user} className={cl.miniImg} />
                                <p>Имя</p>
                            </div>
                            <input 
                                type="name" 
                                placeholder="Иван" 
                                className={cl.inputName} 
                            />
                        </div>
                        <div className={cl.surname}>
                            <div className={cl.textImg}>
                                <img src={user} className={cl.miniImg} />
                                <p>Фамилия</p>
                            </div>
                            <input 
                                type="surname" 
                                placeholder="Иванов" 
                                className={cl.inputSurname} 
                            />
                        </div>
                    </div>
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
                    <div className={cl.confirmPassword}>
                        <img src={confirmPassword} className={cl.miniImg} />
                        <p>Подтверждение пароля</p>
                    </div>
                    <div className={cl.inputContainer}>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Подтвердите пароль"
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
                        Создать аккаунт
                    </button>
                </form>
                <p className={cl.link}>
                    Уже есть аккаунт? <a onClick={() => navigate(AUTH_ROUTE)} >Войти</a>
                </p>
            </div>
        </div>
    )
}

export default RegisterPage