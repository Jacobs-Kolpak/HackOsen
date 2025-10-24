import cl from '../styles/errorpage.module.css'
import cat from '../assets/cat.png'

const ErrorPage = () => {
    return (
        <div className={cl.app}>
            <div className={cl.error}>
                404
            </div>
            <div className={cl.img}>
                <img src={cat} alt="cat" />
                <h1 className={cl.okak}>ОКАК</h1>
            </div>
        </div>
    )
}

export default ErrorPage