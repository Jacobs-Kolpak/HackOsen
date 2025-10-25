import { useState } from 'react'
import cl from '../styles/routespage.module.css'
import users from '../assets/users.svg'
import star from '../assets/star.svg'
import line from '../assets/line.svg'
import clock from '../assets/clockDef.svg'
import upload from '../assets/upload.svg'
import plusUser from '../assets/plusUser.svg'
import usersGreen from '../assets/usersGreen.svg'
import greenDoc from '../assets/greenDoc.svg'

const RoutesPage = () => {
    const [clientId, setClientId] = useState('')
    const [startTime, setStartTime] = useState('')
    const [endTime, setEndTime] = useState('')
    const isValidId = /^\d{4}$/.test(clientId)
    const isFormValid = isValidId && startTime.trim() !== '' && endTime.trim() !== ''

    const handleAddClient = () => {
        if (!isFormValid) return
        alert(`Клиент ${clientId} добавлен!\nИнтервал: ${startTime} — ${endTime}`)
        setClientId('')
        setStartTime('')
        setEndTime('')
    }

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
                        <p className={cl.countClient}>{0}</p>
                        <p className={cl.grayText}>Всего клиентов</p>
                    </div>
                </div>
                <div className={cl.allClients}>
                    <div className={cl.violetBox}>
                        <img src={clock} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{0}</p>
                        <p className={cl.grayText}>Всего клиентов</p>
                    </div>
                </div>
            </div>

            <div className={cl.tabs}>
                <div className={cl.allClients}>
                    <div className={cl.blueBox}>
                        <img src={line} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{0}</p>
                        <p className={cl.grayText}>Всего клиентов</p>
                    </div>
                </div>
                <div className={cl.allClients}>
                    <div className={cl.orangeBox}>
                        <img src={star} className={cl.miniIcon} />
                    </div>
                    <div className={cl.textGreenBox}>
                        <p className={cl.countClient}>{0}</p>
                        <p className={cl.grayText}>Всего клиентов</p>
                    </div>
                </div>
            </div>

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
                <div className={cl.greenBtn}>
                    <p className={cl.loadBtnText}>Загрузить CSV файл</p>
                </div>
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
                    placeholder="0001"
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

            <div className={cl.loadData}>
                <div className={cl.f}>
                    <div className={cl.boxLoad}>
                        <div className={cl.greenWhiteBoxLoad}>
                            <img src={usersGreen} className={cl.miniIcon2} />
                        </div>
                        <div>
                            <p>Список клиентов</p>
                            <p className={cl.textImportGray}>Ожидание загрузки</p>
                        </div>
                    </div>
                </div>

                <div className={cl.containerNoRoute}>
                    <div className={cl.greenBorderContainer}>
                        <img src={greenDoc} className={cl.icon} />
                        <p className={cl.noRouteText}>Клиенты не загружены</p>
                        <p className={cl.grayText2}>Загрузите CSV файл для начала работы с маршрутами.</p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default RoutesPage