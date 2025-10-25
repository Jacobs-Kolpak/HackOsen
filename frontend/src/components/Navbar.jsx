import cl from '../styles/navbar.module.css';
import dashboard from '../assets/dashboard.svg';
import map from '../assets/map.svg';
import routes from '../assets/routes.svg';
import settings from '../assets/settings.svg';
import { useLocation, useNavigate } from 'react-router-dom';
import { DASHBOARD_ROUTE, MAP_ROUTE, ROUTES_ROUTE, SETTINGS_ROUTE } from '../configs/consts';

const Navbar = () => {
    const navigate = useNavigate()
    const location = useLocation()
    const currentPath = location.pathname

    return (
        <div className={cl.container}>
            <div 
                onClick={() => navigate(DASHBOARD_ROUTE)} 
                className={`${cl.iconContainer} ${currentPath === DASHBOARD_ROUTE ? cl.active : ''}`}
            >
                <img className={cl.icon} src={dashboard} />
                <p className={cl.iconText}>Панель</p>
            </div>
            <div 
                onClick={() => navigate(ROUTES_ROUTE)} 
                className={`${cl.iconContainer} ${currentPath === ROUTES_ROUTE ? cl.active : ''}`}
            >
                <img className={cl.icon} src={routes}/>
                <p className={cl.iconText}>Маршруты</p>
            </div>
            <div 
                onClick={() => navigate(MAP_ROUTE)} 
                className={`${cl.iconContainer} ${currentPath === MAP_ROUTE ? cl.active : ''}`}
            >
                <img className={cl.icon} src={map}/>
                <p className={cl.iconText}>Карта</p>
            </div>
            <div 
                onClick={() => navigate(SETTINGS_ROUTE)} 
                className={`${cl.iconContainer} ${currentPath === SETTINGS_ROUTE ? cl.active : ''}`}
            >
                <img className={cl.icon} src={settings}/>
                <p className={cl.iconText}>Настройки</p>
            </div>
        </div>
    )
}

export default Navbar