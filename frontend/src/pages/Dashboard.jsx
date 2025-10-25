import cl from '../styles/dashboard.module.css';
import users from '../assets/users.svg';
import cursor from '../assets/cursor.svg';
import clock from '../assets/clockDef.svg';
import stroke from '../assets/stroke.svg';
import iconMap from '../assets/iconMap.svg'

const stats = [
    { title: 'Всего клиентов', value: 0, containerClass: cl.greenContainer, img: users },
    { title: 'Общая дистанция', value: '0 км', containerClass: cl.blueContainer, img: cursor },
    { title: 'Общее время', value: '0ч 0м', containerClass: cl.orangeContainer, img: clock },
    { title: 'Общее время', value: '10:10', containerClass: cl.violetContainer, img: stroke },
]

const StatCard = ({ title, value, containerClass, img }) => (
    <div className={cl.cardStat}>
        <div>
            <p className={cl.allClients}>{title}</p>
            <p className={cl.textClients}>{value}</p>
        </div>
        <div className={containerClass}>
            <img className={cl.imgClients} src={img} />
        </div>
    </div>
)

const Dashboard = () => (
    <div className={cl.container}>
        <div className={cl.card}>
            <h1 className={cl.titleCard}>Панель управления</h1>
            <p className={cl.textCard}>Обзор маршрутов на сегодня</p>
        </div>
        {stats.map((stat, index) => (
            <StatCard key={index} {...stat} />
        ))}
        <div className={cl.containerNoRoute}>
            <div className={cl.greenBorderContainer}>
                <img src={iconMap} className={cl.icon} />
                <p className={cl.noRouteText}>Маршрут еще не создан</p>
                <p className={cl.grayText}>Перейдите в Планировщик маршрутов, чтобы загрузить список клиентов и создать оптимальный маршрут.</p>
                <p className={cl.greenText}>Начните планирование прямо сейчас</p>
            </div>
        </div>
    </div>
)

export default Dashboard