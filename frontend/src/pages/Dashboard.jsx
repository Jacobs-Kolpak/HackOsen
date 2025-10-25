import cl from '../styles/dashboard.module.css';
import users from '../assets/users.svg';
import cursor from '../assets/cursor.svg';
import clock from '../assets/clockDef.svg';
import stroke from '../assets/stroke.svg';
import iconMap from '../assets/iconMap.svg'
import { useState } from 'react';

function degreesToRadians(degrees) {
    return degrees * (Math.PI / 180);
}

function distanceInKmBetweenEarthCoordinates(lat1, lon1, lat2, lon2) {
    const earthRadiusKm = 6371;
    const dLat = degreesToRadians(lat2 - lat1);
    const dLon = degreesToRadians(lon2 - lon1);
    lat1 = degreesToRadians(lat1);
    lat2 = degreesToRadians(lat2);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return earthRadiusKm * c;
}

function calculateTotalDistance(clients) {
    if (clients.length < 2) return 0;
    let totalDist = 0;
    for (let i = 0; i < clients.length - 1; i++) {
        const c1 = clients[i];
        const c2 = clients[i + 1];
        if (c1.lat && c1.lon && c2.lat && c2.lon) {
            totalDist += distanceInKmBetweenEarthCoordinates(
                parseFloat(c1.lat),
                parseFloat(c1.lon),
                parseFloat(c2.lat),
                parseFloat(c2.lon)
            );
        }
    }
    return Math.round(totalDist);
}

function calculateTotalTime(clients) {
    const numClients = clients.length;
    if (numClients === 0) return '0ч 0м';
    const serviceTimePerClient = 30; // min
    const totalServiceTime = numClients * serviceTimePerClient;
    const totalDist = calculateTotalDistance(clients);
    const averageSpeed = 50; // km/h
    const travelTimeHours = totalDist / averageSpeed;
    const travelTimeMin = travelTimeHours * 60;
    const totalMin = totalServiceTime + travelTimeMin;
    const hours = Math.floor(totalMin / 60);
    const mins = Math.round(totalMin % 60);
    return `${hours}ч ${mins}м`;
}

function parseTotalTimeToMin(totalTimeStr) {
    const [hoursStr, minsStr] = totalTimeStr.split('ч ');
    const hours = parseInt(hoursStr, 10);
    const mins = parseInt(minsStr.replace('м', ''), 10);
    return hours * 60 + mins;
}

function calculateEndTime(clients) {
    if (clients.length === 0) return '10:10';
    const startTime = '09:00';
    const [startHour, startMin] = startTime.split(':').map(Number);
    let totalMin = startHour * 60 + startMin;
    const totalTimeMin = parseTotalTimeToMin(calculateTotalTime(clients));
    totalMin += totalTimeMin;
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

    const totalClients = clients.length;
    const totalDistance = calculateTotalDistance(clients) + ' км';
    const totalTime = calculateTotalTime(clients);
    const endTime = calculateEndTime(clients);

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
            </div>
            {stats.map((stat, index) => (
                <StatCard key={index} {...stat} />
            ))}
            {clients.length === 0 ? (
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