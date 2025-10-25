import React, { useContext } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { privateRoutes, publicRoutes } from "../configs/routes";
import { AUTH_ROUTE, DASHBOARD_ROUTE, ERROR_ROUTE } from "../configs/consts";
import { UserContext } from '../context/UserContext'

const ProtectedRoute = ({ children }) => {
    const { isAuth } = useContext(UserContext);
    if (!isAuth) {
        return <Navigate to={AUTH_ROUTE} />;
    }
    return children;
};

const PublicRoute = ({ children }) => {
    const { isAuth } = useContext(UserContext);
    if (isAuth) {
        return <Navigate to={DASHBOARD_ROUTE} />;
    }
    return children;
};

const AppRouter = () => {
    return (
        <Routes>
            {publicRoutes.map(({ path, Component }) => (
                <Route
                    key={path}
                    path={path}
                    element={
                        <PublicRoute>
                            <Component />
                        </PublicRoute>
                    }
                />
            ))}
            {privateRoutes.map(({ path, Component }) => (
                <Route
                    key={path}
                    path={path}
                    element={
                        <ProtectedRoute>
                            <Component />
                        </ProtectedRoute>
                    }
                />
            ))}
            <Route path="*" element={<Navigate to={ERROR_ROUTE} />} />
        </Routes>
    );
};

export default AppRouter;