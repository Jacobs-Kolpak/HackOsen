import cl from '../styles/routespage.module.css'

const RoutesPage = () => {
    return (
        <div className={cl.container}>
            <h1>Планировщик маршрутов</h1>
            <p className={cl.textHead}>Загрузите список клиентов и оптимизируйте ежедневный маршрут</p>

            <div className={cl.containerGray}>
                <p className={cl.textContainerGray}>Управление клиентами</p>
                
            </div>
        </div>
    )
}

export default RoutesPage