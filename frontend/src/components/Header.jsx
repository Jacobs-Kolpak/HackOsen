import cl from '../styles/header.module.css';
import logo from '../assets/logo.svg';

const Header = () => {
    return (
        <div className={cl.container}>
            <img src={logo} className={cl.logo} />
        </div>
    )
}

export default Header