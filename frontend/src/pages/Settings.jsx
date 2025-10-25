import { useEffect, useState, useContext } from 'react'
import cl from '../styles/settings.module.css'
import user from '../assets/userGreen.svg'
import logoutIcon from '../assets/logoutRed.svg'
import { Profile } from '../api/userApi'
import { UserContext } from '../context/UserContext'

const Settings = () => {
    const [userData, setUserData] = useState(null)
    const { logout } = useContext(UserContext)

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const response = await Profile()
                console.log('Profile response:', response)
                setUserData(response)
            } catch (error) {
                console.error('Ошибка получения пользователя:', error)
            }
        }

        fetchUser()
    }, [])

    const initials = userData ? `${userData.first_name[0]}${userData.last_name[0]}` : ''

    return (
        <div className={cl.container}>
            <h1>Настройки</h1>
            <p className={cl.grayText}>Управление профилем и настройками приложения</p>
            <div className={cl.grayContainer}>
                {userData && (
                    <div className={cl.containerAccount}>
                        <div className={cl.accountCircle}>
                            <p className={cl.accountTwoLetters}>{initials}</p>
                        </div>
                        <p className={cl.nameSurname}>{userData.first_name} {userData.last_name}</p>
                        <p className={cl.role}>Предприниматель</p>

                        <div className={cl.inputs}>
                            <p>Email</p>
                            <input
                                type="email"
                                value={userData.email}
                                disabled={true}
                                className={cl.input}
                            />
                            <p>Город</p>
                            <input
                                type="text"
                                value='Ростов-на-дону'
                                disabled={true}
                                className={cl.input}
                            />
                        </div>
                    </div>
                )}

                <div className={cl.logoutButton} onClick={logout}>
                    <img src={logoutIcon} className={cl.miniIcon} />
                    <p className={cl.logoutText}>Выйти из аккаунта</p>
                </div>
            </div>
        </div>
    )
}

export default Settings