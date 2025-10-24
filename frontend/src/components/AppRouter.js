import React, { useContext } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { privateRoutes, publicRoutes } from "../routes";
import { DASHBOARD_ROUTE, ERROR_ROUTE } from "./consts";
import { UserContext } from '../context/UserContext'

const AppRouter = () => {
    const {isAuth} = useContext(UserContext)

    return (
        <Routes>
            {isAuth ? (
                <>
                    {privateRoutes.map(({ path, Component }) => (
                        <Route key={path} path={path} element={<Component />} />
                    ))}
                    <Route path="*" element={<Navigate to={DASHBOARD_ROUTE}/>} />
                </>
            ) : (
                <>
                    {publicRoutes.map(({ path, Component }) => (
                        <Route key={path} path={path} element={<Component />} />
                    ))}
                    <Route path="*" element={<Navigate to={ERROR_ROUTE}/>} />
                </>
            )}
        </Routes>
    );
};

export default AppRouter;