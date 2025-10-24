import { Component } from "react";
import AuthPage from "../pages/AuthPage";
import MapPage from "../pages/MapPage";
import RoutesPage from "../pages/RoutesPage";
import Settings from "../pages/Settings";
import Dashboard from "../pages/Dashboard";
import ErrorPage from "../pages/ErrorPage";
import { AUTH_ROUTE, DASHBOARD_ROUTE, SETTINGS_ROUTE, MAP_ROUTE, ROUTES_ROUTE, ERROR_ROUTE } from "./consts";

export const publicRoutes = [
    {
        path: AUTH_ROUTE,
        Component: AuthPage
    },
    {
        path: ERROR_ROUTE,
        Component: ErrorPage,
    }
]

export const privateRoutes = [
    {
        path: DASHBOARD_ROUTE,
        Component: Dashboard
    },
    {
        path: SETTINGS_ROUTE,
        Component: Settings
    },
    {
        path: MAP_ROUTE,
        Component: MapPage
    },
    {
        path: ROUTES_ROUTE,
        Component: RoutesPage
    },
]