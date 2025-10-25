// RoutesPage.jsx

import { useState, useEffect } from 'react'
import cl from '../styles/routespage.module.css'
import { useNavigate } from 'react-router-dom'; // Add this if using react-router for navigation

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
import { uploadDataset, getDatasets, optimizeRoute, clearAllDatasets, getClient, updateMeeting } from '../api/userApi.js'; // Add updateMeeting import

const RoutesPage = () => {
    const navigate = useNavigate(); // For redirecting to login if unauthorized
    const [clientId, setClientId] = useState('')
    const [startTime, setStartTime] = useState('09:00')
    const [endTime, setEndTime] = useState('18:00')
    const [clients, setClients] = useState(() => {
        const stored = localStorage.getItem('clients')
        return stored ? JSON.parse(stored) : []
    })
    const [meetingResults, setMeetingResults] = useState({}) // New state: { clientNumber: 'pending' | 'success' | 'failed' }
    const [optimizedRoute, setOptimizedRoute] = useState(null)
    const [errorMessage, setErrorMessage] = useState('') // For displaying errors to user
    const [selectedClientNumber, setSelectedClientNumber] = useState('') // For selecting client by ID
    const [selectedClient, setSelectedClient] = useState(null) // For storing selected client details
    const [isAddingClient, setIsAddingClient] = useState(false) // Loading state for add client
    const [searchTerm, setSearchTerm] = useState('') // New state for search

    useEffect(() => {
        const fetchClients = async () => {
            try {
                const data = await getDatasets();
                const fetchedClients = data.datasets || data || [];
                setClients(fetchedClients);
                localStorage.setItem('clients', JSON.stringify(fetchedClients));
                setErrorMessage(''); // Clear any previous errors
            } catch (err) {
                console.error('Ошибка загрузки клиентов:', err);
                if (err.response?.status === 401) {
                    setErrorMessage('Unauthorized access. Please log in.');
                    navigate('/login'); // Redirect to login page
                } else {
                    setErrorMessage('Error loading clients. Please try again.');
                }
                setClients([]);
                localStorage.setItem('clients', JSON.stringify([]));
            }
        };

        fetchClients();
    }, [navigate]);

    // Load meeting results from localStorage if available
    useEffect(() => {
        const storedResults = localStorage.getItem('meetingResults');
        if (storedResults) {
            setMeetingResults(JSON.parse(storedResults));
        }
    }, []);

    // Save meeting results to localStorage on change
    useEffect(() => {
        localStorage.setItem('meetingResults', JSON.stringify(meetingResults));
    }, [meetingResults]);

    const isValidId = /^\d{4}$/.test(clientId)
    const isFormValid = isValidId && startTime.trim() !== '' && endTime.trim() !== ''
    const isSelectedIdValid = /^\d+$/.test(selectedClientNumber) // Allow any digits, will pad

    const handleMeetingResult = async (clientNumber, clickedResult) => {
        const numericClientNumber = clientNumber.toString(); // Ensure string
        const currentResult = meetingResults[numericClientNumber] || 'pending';
        let newResult;

        if (currentResult === 'pending') {
            // Set to clicked result
            newResult = clickedResult;
        } else if (currentResult === clickedResult) {
            // Toggle off: reverse the rating by sending opposite, then set to pending
            const oppositeSuccess = clickedResult === 'success'; // If clicked 'success', opposite is false; else true
            try {
                await updateMeeting(numericClientNumber, !oppositeSuccess); // Send opposite: if was success, send false; if failed, send true
                console.log(`Reversed meeting for client ${numericClientNumber}: sent ${!oppositeSuccess}`);
                newResult = 'pending'; // After successful reverse, set to pending
            } catch (err) {
                console.error('Error reversing meeting:', err);
                setErrorMessage('Error reversing meeting status. Please try again.');
                return; // Do not change state on error
            }
        } else {
            // Switch to new result
            newResult = clickedResult;
        }

        // Update local state (for pending case or switch, or after successful reverse)
        setMeetingResults(prev => ({ ...prev, [numericClientNumber]: newResult }));

        // Call API only if not pending (for set or switch)
        if (newResult !== 'pending') {
            try {
                await updateMeeting(numericClientNumber, newResult === 'success');
                console.log(`Meeting updated for client ${numericClientNumber}: ${newResult}`);
            } catch (err) {
                console.error('Error updating meeting:', err);
                setErrorMessage('Error updating meeting status. Please try again.');
                // Revert local state on error
                setMeetingResults(prev => ({ ...prev, [numericClientNumber]: currentResult }));
                return;
            }
        }

        // Clear error if success
        setErrorMessage('');
    };

    const handleAddClient = async () => {
        if (!isFormValid) return
        setIsAddingClient(true)
        setErrorMessage('') // Clear previous errors

        const paddedClientId = clientId.padStart(4, '0');
        let clientDetails = null;

        try {
            // Fetch client details (works for VIP clients)
            clientDetails = await getClient(paddedClientId);
            console.log('Fetched client details:', clientDetails);
        } catch (fetchErr) {
            console.warn('Could not fetch client details (possibly not VIP):', fetchErr);
            // Continue with standard client, empty address
            clientDetails = {
                adress: '',
                is_vip: false,
                start: startTime,
                end: endTime
            };
        }

        // Use fetched or default values
        const address = clientDetails.adress || '';
        const level = clientDetails.is_vip ? 'vip' : 'standard';
        // Use input times, override with fetched if available (but inputs are provided, so prioritize inputs)
        const finalStart = startTime;
        const finalEnd = endTime;

        // Russian headers based on error message
        const headers = 'Номер объекта,Адрес,Широта,Долгота,Динамический критерий,Время начала работы,Время окончания работы,Время начала обеда,Время окончания обеда,Уровень клиента';
        // Data row with fetched address, empty lat/lng, dynamic=0, no lunch, level from details
        const dataRow = `${paddedClientId},${address},,,0,${finalStart},${finalEnd},,${level}`;

        // Create CSV content
        const csvContent = `${headers}\n${dataRow}`;

        // Create Blob as file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const file = new File([blob], `client_${paddedClientId}.csv`, { type: 'text/csv' });

        try {
            await uploadDataset(file);
            const data = await getDatasets();
            const parsedClients = data.datasets || data || [];
            setClients(parsedClients)
            localStorage.setItem('clients', JSON.stringify(parsedClients))
        } catch (err) {
            console.error('Ошибка добавления клиента:', err);
            if (err.response?.status === 401) {
                setErrorMessage('Unauthorized access. Please log in.');
                navigate('/login'); // Redirect to login page
            } else if (err.response?.status === 400) {
                setErrorMessage('Ошибка формата CSV. Убедитесь, что данные корректны.');
            } else {
                setErrorMessage('Error adding client. Please try again.');
            }
        } finally {
            setIsAddingClient(false)
            setClientId('')
            setStartTime('09:00')
            setEndTime('18:00')
        }
    }

    const handleFileUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        try {
            await uploadDataset(file);
            const data = await getDatasets();
            const parsedClients = data.datasets || data || [];
            setClients(parsedClients)
            localStorage.setItem('clients', JSON.stringify(parsedClients))
            setErrorMessage(''); // Clear any previous errors
        } catch (err) {
            console.error('Ошибка загрузки файла:', err);
            if (err.response?.status === 401) {
                setErrorMessage('Unauthorized access. Please log in.');
                navigate('/login'); // Redirect to login page
            } else {
                setErrorMessage('Error uploading file. Please try again.');
            }
        }
    }

    const handleClearClients = async () => {
        if (clients.length === 0) return
        if (window.confirm('Вы уверены, что хотите очистить список клиентов?')) {
            try {
                await clearAllDatasets(); // Удаляем с сервера
                const data = await getDatasets(); // Перефетчим, чтобы обновить состояние
                const fetchedClients = data.datasets || data || [];
                setClients(fetchedClients);
                localStorage.setItem('clients', JSON.stringify(fetchedClients));
                setOptimizedRoute(null); // Очистка оптимизированного маршрута
                setMeetingResults({}); // Clear meeting results
                localStorage.removeItem('meetingResults');
                setErrorMessage(''); // Очищаем ошибки, если были
                setSelectedClient(null); // Очищаем выбранного клиента
                setSelectedClientNumber('');
            } catch (err) {
                console.error('Ошибка очистки клиентов:', err);
                if (err.response?.status === 401) {
                    setErrorMessage('Unauthorized access. Please log in.');
                    navigate('/login'); // Redirect to login page
                } else {
                    setErrorMessage('Error clearing clients. Please try again.');
                }
            }
        }
    }

    const handleOptimizeRoute = async () => {
    try {
        const data = await optimizeRoute();
        console.log('Данные с оптимизации:', data); // Вывод значений в консоль
        setOptimizedRoute(data);
        localStorage.setItem('optimizedRoute', JSON.stringify(data)); // Save to localStorage for Dashboard
    } catch (err) {
            console.error('Ошибка оптимизации маршрута:', err);
            if (err.response?.status === 401) {
                setErrorMessage('Unauthorized access. Please log in.');
                navigate('/login'); // Redirect to login page
            } else {
                setErrorMessage('Error optimizing route. Please try again.');
            }
        }
    }

    const handleGetClientDetails = async () => {
        if (!isSelectedIdValid) {
            setErrorMessage('ID клиента должен состоять из цифр');
            return;
        }
        const paddedClientNumber = selectedClientNumber.padStart(4, '0');
        
        // Проверка в локальном списке (быстрый фоллбэк)
        const localClient = clients.find(c => 
            (c.clients?.[0]?.client_number || c.object_number || c.id || '').toString().padStart(4, '0') === paddedClientNumber
        );
        if (localClient && !localClient.is_vip) {
            setErrorMessage(`Клиент ${paddedClientNumber} найден локально, но это стандартный клиент. Детали VIP доступны только через API.`);
            setSelectedClient({
                client_number: paddedClientNumber,
                adress: localClient.address || 'Не указан',
                is_vip: false,
                rating: 'N/A (стандартный)'
            });
            return;
        }

        try {
            const data = await getClient(paddedClientNumber);
            setSelectedClient(data);
            setErrorMessage(''); // Clear any previous errors
        } catch (err) {
            console.error('Ошибка загрузки деталей клиента:', err);
            if (err.response?.status === 401) {
                setErrorMessage('Unauthorized access. Please log in.');
                navigate('/login');
            } else if (err.response?.status === 404 || err.response?.status === 422) {
                // Улучшенное сообщение для 422
                const detailMsg = err.response?.data?.detail?.[0]?.msg || 'не найден';
                setErrorMessage(`Клиент ${paddedClientNumber} ${detailMsg}. Эндпоинт работает только для VIP клиентов. Если клиент VIP, проверьте ID на бэкенде напрямую (БД или Postman).`);
            } else {
                setErrorMessage('Error loading client details. Please try again.');
            }
            setSelectedClient(null);
        }
    }

    const handleExportMeetingReport = () => {
        if (clients.length === 0) {
            setErrorMessage('Нет данных для экспорта');
            return;
        }

        const headers = ['Номер', 'Имя клиента', 'Адрес', 'Статус клиента', 'Время встречи', 'Результат встречи'];
        const rows = displayClients.map((client) => {
            const clientNumber = client.clients && client.clients[0] ? client.clients[0].client_number.padStart(4, '0') : (client.object_number || client.id || '').toString().padStart(4, '0');
            const level = (client.client_level || '').toLowerCase() === 'vip' ? 'VIP' : 'Стандарт';
            const start = client.work_start_time || client.start || '';
            const end = client.work_end_time || client.end || '';
            const timeWindow = start && end ? `${start} - ${end}` : '';
            const result = meetingResults[clientNumber] || 'Ожидание';
            const resultDisplay = result === 'success' ? 'Состоялась' : result === 'failed' ? 'Не состоялась' : 'Ожидание';

            return [
                (displayClients.indexOf(client) + 1).toString(),
                `Клиент ${clientNumber}`,
                client.address || '',
                level,
                timeWindow,
                resultDisplay
            ];
        });

        const csvContent = [headers, ...rows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `meeting_report_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        
        setErrorMessage(''); // Clear any errors
        console.log('Отчет о встречах успешно экспортирован');
    };

    const vipCount = clients.filter((c) => (c.client_level || '').toLowerCase() === 'vip').length
    const standardCount = clients.filter((c) => (c.client_level || '').toLowerCase() !== 'vip').length

    const displayClients = optimizedRoute ? optimizedRoute.route_points : clients;

    // Filter clients based on search term (by client number or address)
    const filteredClients = displayClients.filter((client) => {
        const clientNumber = client.clients && client.clients[0] 
            ? client.clients[0].client_number.toString().padStart(4, '0') 
            : (client.object_number || client.id || '').toString().padStart(4, '0');
        const address = (client.address || '').toLowerCase();
        const searchLower = searchTerm.toLowerCase();
        return clientNumber.includes(searchLower) || address.includes(searchLower);
    });

    return (
        <div className={cl.container}>
            {errorMessage && <p className={cl.errorText}>{errorMessage}</p>} {/* Display error to user */}
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
                    disabled={isAddingClient}
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
                    disabled={isAddingClient}
                />

                <p className={cl.topMar}>Конец временного окна</p>
                <input
                    type='time'
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className={cl.inputPasswordTime}
                    disabled={isAddingClient}
                />

                <button
                    className={`${cl.greenBtn2} ${!isFormValid ? cl.disabledBtn : ''}`}
                    disabled={!isFormValid || isAddingClient}
                    onClick={handleAddClient}
                >
                    <p className={cl.loadBtnText}>
                        {isAddingClient ? 'Добавление...' : 'Добавить клиента в список'}
                    </p>
                </button>
            </div>

            {/* === НОВЫЙ БЛОК: Выбор клиента по ID и отображение деталей === */}
            {/* <div className={cl.loadData}>
                <div className={cl.f}>
                    <div className={cl.boxLoad}>
                        <div className={cl.greenBoxLoad}>
                            <img src={usersGreen} className={cl.miniIcon2} />
                        </div>
                        <div>
                            <p>Просмотр деталей клиента</p>
                            <p className={cl.textImportGray}>Введите ID клиента для просмотра адреса и статуса (только VIP)</p>
                        </div>
                    </div>
                </div>

                <p>ID клиента</p>
                <input
                    type='text'
                    placeholder='0001'
                    value={selectedClientNumber}
                    onChange={(e) => setSelectedClientNumber(e.target.value.replace(/\D/g, ''))} // Only digits
                    className={`${cl.inputPassword} ${selectedClientNumber && !isSelectedIdValid ? cl.errorInput : ''}`}
                />
                <p className={cl.textVvod}>Введите ID клиента (цифры, будет дополнено до 4 знаков)</p>
                {selectedClientNumber && !isSelectedIdValid && (
                    <p className={cl.errorText}>ID должен состоять из цифр</p>
                )}

                <button
                    className={`${cl.greenBtn2} ${!isSelectedIdValid ? cl.disabledBtn : ''}`}
                    disabled={!isSelectedIdValid}
                    onClick={handleGetClientDetails}
                >
                    <p className={cl.loadBtnText}>Получить детали клиента</p>
                </button>

                {selectedClient && (
                    <div className={cl.clientDetails}>
                        <h3>Детали клиента {selectedClient.client_number}</h3>
                        <div className={cl.detailRow}>
                            <img src={location} alt="Location" className={cl.detailIcon} />
                            <p><strong>Адрес:</strong> {selectedClient.adress || 'Не указан'}</p>
                        </div>
                        <div className={cl.detailRow}>
                            <img src={star} alt="Status" className={cl.detailIcon} />
                            <p><strong>Статус:</strong> {selectedClient.is_vip ? 'VIP' : 'Стандарт'}</p>
                        </div>
                        <div className={cl.detailRow}>
                            <p><strong>Рейтинг:</strong> {selectedClient.rating || 'Не указан'}</p>
                        </div>
                        <button
                            className={cl.greenBtn2}
                            onClick={() => {
                                setSelectedClient(null);
                                setSelectedClientNumber('');
                            }}
                        >
                            <p className={cl.loadBtnText}>Очистить</p>
                        </button>
                    </div>
                )}
            </div> */}

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
                    <>
                        {clients.length > 0 && (
                            <button
                                className={cl.greenBtn3}
                                onClick={handleOptimizeRoute}
                            >
                                <p className={cl.loadBtnText}>Оптимизировать маршрут</p>
                            </button>
                        )}
                        {/* Search Input */}
                        <input
                            type="text"
                            placeholder="Поиск по ID клиента или адресу"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className={cl.searchInput}
                        />
                        <div className={cl.clientList}>
                            {filteredClients.length > 0 ? (
                                filteredClients.map((client, i) => {
                                    const level = (client.client_level || '').toLowerCase() === 'vip' ? 'vip' : 'standard';
                                    const levelDisplay = level === 'vip' ? 'VIP' : 'Стандарт';
                                    const clientNumber = client.clients && client.clients[0] ? client.clients[0].client_number.padStart(4, '0') : (client.object_number || client.id || '').toString().padStart(4, '0');
                                    const start = client.work_start_time || client.start || '';
                                    const end = client.work_end_time || client.end || '';
                                    const arrivalTime = client.arrival_time ? `Время прибытия: ${client.arrival_time}` : '';
                                    const currentResult = meetingResults[clientNumber] || 'pending';
                                    return (
                                        <div key={i} className={cl.clientCard}>
                                            <div className={cl.clientHeader}>
                                                <div className={cl.greenNumber}>
                                                    {displayClients.indexOf(client) + 1}
                                                </div>
                                                <p className={cl.clientId}>Клиент {clientNumber}</p>
                                                <div className={`${cl.levelBadge} ${level === 'vip' ? cl.orangeBadge : cl.blueBadge}`}>
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
                                            <p className={cl.detailValue}>{start && end ? `${start} - ${end}` : ''}</p>
                                            {arrivalTime && (
                                                <p className={cl.detailValue}>{arrivalTime}</p>
                                            )}
                                            <p className={cl.statusLabel}>Статус встречи</p>
                                            <p className={cl.statusSubLabel}>Если встреча сорвалась не по вине клиента, ничего не выбирайте</p>
                                            <div className={cl.statusOptions}>
                                                <div 
                                                    className={`${cl.statusGreen} ${currentResult === 'success' ? cl.selectedStatus : ''}`}
                                                    onClick={() => handleMeetingResult(clientNumber, 'success')}
                                                >
                                                    <img src={checkGreen} alt="Check" className={cl.statusIcon} />
                                                    Встреча состоялась
                                                </div>
                                                <div 
                                                    className={`${cl.statusRed} ${currentResult === 'failed' ? cl.selectedStatus : ''}`}
                                                    onClick={() => handleMeetingResult(clientNumber, 'failed')}
                                                >
                                                    <img src={xRed} alt="X" className={cl.statusIcon} />
                                                    Встреча не состоялась
                                                </div>
                                            </div>
                                            {currentResult !== 'pending' && (
                                                <p className={cl.statusReset}>Нажмите еще раз для сброса</p>
                                            )}
                                        </div>
                                    );
                                })
                            ) : (
                                <p className={cl.noResults}>Ничего не найдено по запросу "{searchTerm}"</p>
                            )}
                        </div>
                        {optimizedRoute && (
                            <div>
                                <p>Общее расстояние: {optimizedRoute.total_distance}</p>
                                <p>Общее время: {optimizedRoute.total_time_hours} часов {optimizedRoute.total_time_minutes} минут</p>
                                <p>Сообщение: {optimizedRoute.message}</p>
                            </div>
                        )}
                        {/* Download Report Button */}
                        <div className={cl.downloadSection}>
                            <button
                                className={cl.downloadBtn}
                                onClick={handleExportMeetingReport}
                            >
                                <p className={cl.loadBtnText}>Скачать отчет о встречах</p>
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

export default RoutesPage