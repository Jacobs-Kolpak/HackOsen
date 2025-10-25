// Dashboard.jsx

import cl from '../styles/dashboard.module.css';
import users from '../assets/users.svg';
import cursor from '../assets/cursor.svg';
import clock from '../assets/clockDef.svg';
import stroke from '../assets/stroke.svg';
import iconMap from '../assets/iconMap.svg'
import { useState, useEffect } from 'react';

function calculateEndTime(totalHours, totalMinutes) {
    const startTime = '09:00';
    const [startHour, startMin] = startTime.split(':').map(Number);
    let totalMin = startHour * 60 + startMin + (totalHours * 60 + totalMinutes);
    const endHour = Math.floor(totalMin / 60) % 24;
    const endMin = totalMin % 60;
    return `${endHour.toString().padStart(2, '0')}:${endMin.toString().padStart(2, '0')}`;
}

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

const Dashboard = () => {
    const [clients, setClients] = useState(() => {
        const stored = localStorage.getItem('clients')
        return stored ? JSON.parse(stored) : []
    })
    const [optimizedRoute, setOptimizedRoute] = useState(null)

    useEffect(() => {
        const storedOptimized = localStorage.getItem('optimizedRoute')
        if (storedOptimized) {
            setOptimizedRoute(JSON.parse(storedOptimized))
        }
    }, [])

    // Prefer optimized data if available
    const useOptimized = optimizedRoute && optimizedRoute.success
    const totalClients = useOptimized ? optimizedRoute.route_points.length : clients.length
    const totalDistance = useOptimized ? `${optimizedRoute.total_distance} км` : '0 км'
    const totalTime = useOptimized 
        ? `${optimizedRoute.total_time_hours}ч ${optimizedRoute.total_time_minutes}м` 
        : '0ч 0м'
    const endTime = useOptimized 
        ? calculateEndTime(optimizedRoute.total_time_hours, optimizedRoute.total_time_minutes)
        : '10:10'

    const stats = [
        { title: 'Всего клиентов', value: totalClients, containerClass: cl.greenContainer, img: users },
        { title: 'Общая дистанция', value: totalDistance, containerClass: cl.blueContainer, img: cursor },
        { title: 'Общее время', value: totalTime, containerClass: cl.orangeContainer, img: clock },
        { title: 'Окончание', value: endTime, containerClass: cl.violetContainer, img: stroke },
    ]

    return (
        <div className={cl.container}>
            <div className={cl.card}>
                <h1 className={cl.titleCard}>Панель управления</h1>
                <p className={cl.textCard}>Обзор маршрутов на сегодня</p>
                {useOptimized && (
                    <p className={cl.message}>{optimizedRoute.message}</p>
                )}
            </div>
            {stats.map((stat, index) => (
                <StatCard key={index} {...stat} />
            ))}
            {(clients.length === 0 && !useOptimized) ? (
                <div className={cl.containerNoRoute}>
                    <div className={cl.greenBorderContainer}>
                        <img src={iconMap} className={cl.icon} />
                        <p className={cl.noRouteText}>Маршрут еще не создан</p>
                        <p className={cl.grayText}>Перейдите в Планировщик маршрутов, чтобы загрузить список клиентов и создать оптимальный маршрут.</p>
                        <p className={cl.greenText}>Начните планирование прямо сейчас</p>
                    </div>
                </div>
            ) : null}
        </div>
    )
}

export default Dashboard