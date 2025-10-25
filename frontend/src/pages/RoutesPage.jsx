import { useState } from 'react'
import Papa from 'papaparse'
import cl from '../styles/routespage.module.css'

import users from '../assets/users.svg'
import star from '../assets/star.svg'
import line from '../assets/line.svg'
import clock from '../assets/clockDef.svg'
import upload from '../assets/upload.svg'
import plusUser from '../assets/plusUser.svg'
import usersGreen from '../assets/usersGreen.svg'
import greenDoc from '../assets/greenDoc.svg'
import trashRed from '../assets/trashRed.svg'
import location from '../assets/location.svg'
import checkGreen from '../assets/checkGreen.svg'
import xRed from '../assets/xRed.svg'

const RoutesPage = () => {
    const [clientId, setClientId] = useState('')
    const [startTime, setStartTime] = useState('')
    const [endTime, setEndTime] = useState('')
    const [clients, setClients] = useState(() => {
        const stored = localStorage.getItem('clients')
        return stored ? JSON.parse(stored) : []
    })

    const isValidId = /^\d{4}$/.test(clientId)
    const isFormValid = isValidId && startTime.trim() !== '' && endTime.trim() !== ''

    const handleAddClient = () => {
        if (!isFormValid) return
        const newClient = {
            id: clientId,
            start: startTime,
            end: endTime,
            level: 'standart',
        }
        const updatedClients = [...clients, newClient]
        setClients(updatedClients)
        localStorage.setItem('clients', JSON.stringify(updatedClients))
        setClientId('')
        setStartTime('')
        setEndTime('')
    }

    const handleFileUpload = (e) => {
        const file = e.target.files[0]
        if (!file) return

        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                const parsedClients = results.data.map((row) => ({
                    id: row['Номер объекта'] || '',
                    address: row['Адрес объекта'] || '',
                    lat: row['Географическая широта'] || '',
                    lon: row['Географическая долгота'] || '',
                    dynamic: row['Динамический критерий'] || '',
                    start: row['Время начала рабочего дня'] || '',
                    end: row['Время окончания рабочего дня'] || '',
                    lunchStart: row['Время начала обеда'] || '',
                    lunchEnd: row['Время окончания обеда'] || '',
                    level: (row['Уровень клиента'] || '').toLowerCase(),
                }))
                setClients(parsedClients)
                localStorage.setItem('clients', JSON.stringify(parsedClients))
            },
        })
    }

    const handleClearClients = () => {
        if (clients.length === 0) return
        if (window.confirm('Вы уверены, что хотите очистить список клиентов?')) {
            setClients([])
            localStorage.removeItem('clients')
        }
    }

    const vipCount = clients.filter((c) => c.level === 'vip').length
    const standardCount = clients.filter((c) => c.level === 'standart').length

    return (
        <div className={cl.container}>
            <h1>Планировщик маршрутов</h1>
            <p className={cl.textHead}>Загрузите список клиентов и оптимизируйте ежедневный маршрут</p>

            <div className={cl.tabs}>
                <div className={cl.allClients}>
                    <div className={cl.greenBox}>
                        <img src={users} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{clients.length}</p>
                        <p className={cl.grayText}>Всего клиентов</p>
                    </div>
                </div>
                <div className={cl.allClients}>
                    <div className={cl.violetBox}>
                        <img src={clock} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{clients.length > 0 ? `${clients.length * 30} мин` : 0}</p>
                        <p className={cl.grayText}>Общее время (примерно)</p>
                    </div>
                </div>
            </div>

            <div className={cl.tabs}>
                <div className={cl.allClients}>
                    <div className={cl.blueBox}>
                        <img src={line} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{standardCount}</p>
                        <p className={cl.grayText}>Стандарт</p>
                    </div>
                </div>
                <div className={cl.allClients}>
                    <div className={cl.orangeBox}>
                        <img src={star} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{vipCount}</p>
                        <p className={cl.grayText}>VIP клиенты</p>
                    </div>
                </div>
            </div>

            {/* === ЗАГРУЗКА CSV === */}
            <div className={cl.loadData}>
                <div className={cl.f}>
                    <div className={cl.boxLoad}>
                        <div className={cl.greenBoxLoad}>
                            <img src={upload} className={cl.miniIcon2} />
                        </div>
                        <div>
                            <p>Загрузка данных</p>
                            <p className={cl.textImportGray}>Импортируйте список клиентов</p>
                        </div>
                    </div>
                </div>
                <label className={cl.greenBtn}>
                    <p className={cl.loadBtnText}>Загрузить CSV файл</p>
                    <input
                        type='file'
                        accept='.csv'
                        onChange={handleFileUpload}
                        style={{display: 'none'}}
                    />
                </label>
            </div>

            <div className={cl.loadData}>
                <div className={cl.f}>
                    <div className={cl.boxLoad}>
                        <div className={cl.greenBoxLoad}>
                            <img src={plusUser} className={cl.miniIcon2} />
                        </div>
                        <div>
                            <p>Добавление клиента вручную</p>
                            <p className={cl.textImportGray}>Введите данные клиента для добавления в маршрут</p>
                        </div>
                    </div>
                </div>

                <p>ID клиента</p>
                <input
                    type='text'
                    placeholder='0001'
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    className={`${cl.inputPassword} ${clientId && !isValidId ? cl.errorInput : ''}`}
                />
                <p className={cl.textVvod}>Введите четырёхзначный ID клиента</p>
                {clientId && !isValidId && (
                    <p className={cl.errorText}>ID должен состоять из 4 цифр</p>
                )}

                <p className={cl.topMar}>Начало временного окна</p>
                <input
                    type='time'
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className={cl.inputPasswordTime}
                />

                <p className={cl.topMar}>Конец временного окна</p>
                <input
                    type='time'
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className={cl.inputPasswordTime}
                />

                <button
                    className={`${cl.greenBtn2} ${!isFormValid ? cl.disabledBtn : ''}`}
                    disabled={!isFormValid}
                    onClick={handleAddClient}
                >
                    <p className={cl.loadBtnText}>Добавить клиента в список</p>
                </button>
            </div>

            {clients.length !== 0 ? (
                <div className={cl.loadData}>
                    <div className={cl.f}>
                        <div className={cl.boxLoad}>
                            <div className={cl.redBoxLoad}>
                                <img src={trashRed} className={cl.miniIcon2} />
                            </div>
                            <div>
                                <p>Очистить данные</p>
                                <p className={cl.textImportGray}>
                                    Удалить все добавленных клиентов
                                </p>
                            </div>
                        </div>
                    </div>
                    <button
                        className={cl.greenBtn3}
                        onClick={handleClearClients}
                    >
                        <p className={cl.loadBtnText}>Очистить список клиентов</p>
                    </button>
                </div>
            ) : (
                <></>
            )}

            <div className={cl.loadData}>
                <div className={cl.f}>
                    <div className={cl.boxLoad}>
                        <div className={cl.greenWhiteBoxLoad}>
                            <img src={usersGreen} className={cl.miniIcon2} />
                        </div>
                        <div>
                            <p>Список клиентов</p>
                            <p className={cl.textImportGray}>
                                {clients.length > 0 ? `Загружено ${clients.length}` : 'Ожидание загрузки'}
                            </p>
                        </div>
                    </div>
                </div>

                {clients.length === 0 ? (
                    <div className={cl.containerNoRoute}>
                        <div className={cl.greenBorderContainer}>
                            <img src={greenDoc} className={cl.icon} />
                            <p className={cl.noRouteText}>Клиенты не загружены</p>
                            <p className={cl.grayText2}>Загрузите CSV файл для начала работы с маршрутами.</p>
                        </div>
                    </div>
                ) : (
                    <div className={cl.clientList}>
                        {clients.map((client, i) => {
                            const levelDisplay = client.level === 'vip' ? 'VIP' : 'Стандарт';
                            return (
                                <div key={i} className={cl.clientCard}>
                                    <div className={cl.clientHeader}>
                                        <div className={cl.greenNumber}>
                                            {i + 1}
                                        </div>
                                        <p className={cl.clientId}>Клиент {client.id.padStart(4, '0')}</p>
                                        <div className={`${cl.levelBadge} ${client.level === 'vip' ? cl.orangeBadge : cl.blueBadge}`}>
                                            {levelDisplay}
                                        </div>
                                    </div>
                                    <div className={cl.clientDetailRow}>
                                        <img src={location} alt="Location" className={cl.detailIcon} />
                                        <p className={cl.detailLabel}>Адрес</p>
                                    </div>
                                    <p className={cl.detailValue}>{client.address || ''}</p>
                                    <div className={cl.clientDetailRow}>
                                        <img src={clock} alt="Clock" className={cl.detailIcon} />
                                        <p className={cl.detailLabel}>Временное окно</p>
                                    </div>
                                    <p className={cl.detailValue}>{client.start ? `${client.start} - ${client.end}` : ''}</p>
                                    <p className={cl.statusLabel}>Статус встречи</p>
                                    <div className={cl.statusOptions}>
                                        <div className={cl.statusGreen}>
                                            <img src={checkGreen} alt="Check" className={cl.statusIcon} />
                                            Встреча состоялась
                                        </div>
                                        <div className={cl.statusRed}>
                                            <img src={xRed} alt="X" className={cl.statusIcon} />
                                            Встреча не состоялась
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}

export default RoutesPage