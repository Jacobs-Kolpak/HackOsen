import cl from '../styles/header.module.css';
import logo from '../assets/logo.svg';

const Header = () => {
    return (
        <div className={cl.container}>
            <img src={logo} className={cl.logo} />
            <div className={cl.textContainer}>
                <h1 className={cl.title}>Оптимизатор Маршрутов AI</h1>
                <p className={cl.subtitle}>Планирование на основе GNN</p>
            </div>
        </div>
    )
}

export default Header