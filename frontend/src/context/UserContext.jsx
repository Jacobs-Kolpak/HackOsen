import React, { createContext, useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";

export const UserContext = createContext()

const UserContextProvider = ({children}) => {
    const [isAuth, setIsAuth] = useState(false)
    const [user, setUser] = useState({})
    const navigate = useNavigate()

    useEffect(() => {
        const storedIsAuth = localStorage.getItem('isAuth')
        const storedUser = localStorage.getItem('user')
        if (storedIsAuth && storedUser) {
            setIsAuth(JSON.parse(storedIsAuth))
            setUser(JSON.parse(storedUser))
        }
    }, [])

    const login = (userData) => {
        if (!isAuth || JSON.stringify(user) !== JSON.stringify(userData)) {
            setIsAuth(true)
            setUser(userData)
            localStorage.setItem('isAuth', JSON.stringify(true))
            localStorage.setItem('user', JSON.stringify(userData))
        }
    }

    const registration = (userData) => {
        if (!isAuth || JSON.stringify(user) !== JSON.stringify(userData)) {
            setIsAuth(true)
            setUser(userData)
            localStorage.setItem('isAuth', JSON.stringify(true))
            localStorage.setItem('user', JSON.stringify(userData))
        }
    }

    const logout = () => {
        setIsAuth(false)
        setUser({})
        localStorage.removeItem('isAuth')
        localStorage.removeItem('user')
        localStorage.removeItem('token')
        navigate('/auth')
    }

    const contextValue = useMemo(() => ({
        isAuth,
        user,
        login,
        logout,
        registration,
    }), [isAuth, user])

    return (
        <UserContext.Provider value={contextValue}>
            {children}
        </UserContext.Provider>
    )
}

export default UserContextProvider