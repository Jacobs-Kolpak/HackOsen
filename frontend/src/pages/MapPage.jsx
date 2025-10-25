import React, { useState } from 'react';
import RouteEditor from './RouteEditor.jsx'; // Импорт из созданного файла (уточните путь, если нужно)
import '../styles/mainpage.css';

const MapPage = () => {
  const [savedOrder, setSavedOrder] = useState([]);

  const testPoints = [
    { id: 1, lat: 47.221532, lng: 39.704423, address: "344011, г. Ростов-на-Дону, ул. Большая Садовая, д. 1" },
    { id: 2, lat: 47.228945, lng: 39.718762, address: "344002, г. Ростов-на-Дону, пр. Буденновский, д. 15" },
    { id: 3, lat: 47.235671, lng: 39.689543, address: "344019, г. Ростов-на-Дону, ул. Красноармейская, д. 67" },
    { id: 4, lat: 47.246892, lng: 39.723456, address: "344025, г. Ростов-на-Дону, пр. Ворошиловский, д. 32" },
    { id: 5, lat: 47.258743, lng: 39.745672, address: "344037, г. Ростов-на-Дону, ул. Таганрогская, д. 124" },
    { id: 6, lat: 47.218765, lng: 39.712345, address: "344009, г. Ростов-на-Дону, ул. Пушкинская, д. 89" },
    { id: 7, lat: 47.231234, lng: 39.698765, address: "344015, г. Ростов-на-Дону, пр. Стачки, д. 45" },
    { id: 8, lat: 47.267890, lng: 39.734567, address: "344038, г. Ростов-на-Дону, ул. Малиновского, д. 76" },
    { id: 9, lat: 47.223456, lng: 39.726789, address: "344006, г. Ростов-на-Дону, ул. Горького, д. 23" },
    { id: 10, lat: 47.245678, lng: 39.712398, address: "344029, г. Ростов-на-Дону, ул. Социалистическая, д. 54" }
  ];

  const handleSave = (newOrder) => {
    setSavedOrder(newOrder);
    console.log('Сохранённый порядок:', newOrder.map(p => ({ id: p.id, address: p.address })));
  };

  return (
    <div className="container">
      <div className="header">
        <h1 className="h1">Редактор маршрута</h1>
        <p className="textHead">Перетаскивай точки для изменения порядка. Маршрут обновится.</p>
      </div>
      
      <RouteEditor points={testPoints} onSave={handleSave} />
      
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