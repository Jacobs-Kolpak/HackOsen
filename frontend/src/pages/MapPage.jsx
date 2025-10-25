import React, { useState, useEffect } from 'react';
import RouteEditor from './RouteEditor.jsx';
import { getOptimizedRoute } from '../api/userApi.js';
import '../styles/mainpage.css';

const MapPage = () => {
  const [savedOrder, setSavedOrder] = useState([]);
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPoints = async () => {
      try {
        const routePoints = await getOptimizedRoute();
        setPoints(routePoints);
      } catch (err) {
        setError(err.message || 'Ошибка загрузки маршрута');
      } finally {
        setLoading(false);
      }
    };

    fetchPoints();
  }, []);

  const handleSave = (newOrder) => {
    setSavedOrder(newOrder);
    console.log('Сохранённый порядок:', newOrder.map(p => ({ id: p.id, address: p.address })));
  };

  if (loading) {
    return <div>Загрузка маршрута...</div>;
  }

  if (error) {
    return <div>Ошибка: {error}</div>;
  }

  return (
    <div className="container">
      <div className="header">
        <h1 className="h1">Редактор маршрута</h1>
        <p className="textHead">Перетаскивай точки для изменения порядка. Маршрут обновится.</p>
      </div>
      
      <RouteEditor points={points} onSave={handleSave} />
      
      {savedOrder.length > 0 && (
        <div className="saved-section">
          <h3 className="grayText">Сохранённый порядок:</h3>
          <ul className="saved-list">
            {savedOrder.map((point, idx) => (
              <li key={point.id} className="saved-item">
                <span className="point-number">{idx + 1}.</span>
                <span className="point-address">{point.address}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MapPage;