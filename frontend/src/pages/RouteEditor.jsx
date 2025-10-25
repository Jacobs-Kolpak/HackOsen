// components/RouteEditor.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import '../styles/routeeditor.css';

import { getOptimizedMap } from '../api/userApi.js';

function SortableItem({ id, index, address }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    display: 'flex',
    alignItems: 'center',
    padding: '12px',
    margin: '4px',
    background: '#f9f9f9',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'grab',
  };

  return (
    <li ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <span style={{ marginRight: '10px', fontSize: '16px', color: '#666' }}>⋮⋮</span>
      {index + 1}. {address}
    </li>
  );
}

const RouteEditor = ({ points = [], onSave = () => {} }) => {
  const [order, setOrder] = useState([]);
  const [mapHtml, setMapHtml] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const transformedPoints = React.useMemo(() => {
    return points.map(point => ({
      id: point.object_number || point.id,
      lat: point.latitude || point.lat,
      lng: point.longitude || point.lng,
      address: point.address || 'Неизвестный адрес',
    }));
  }, [points]);

  useEffect(() => {
    setOrder(transformedPoints);
  }, [transformedPoints]);

  const fetchMap = useCallback(async () => {
    if (points.length === 0) {
      setMapHtml('');
      setError('');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      console.log('Генерация карты... (10-15 сек)');
      const html = await getOptimizedMap();
      console.log('HTML получен, длина:', html.length);
      setMapHtml(html);
    } catch (err) {
      console.error('Ошибка загрузки карты:', err);
      setError(err.message || 'Неизвестная ошибка');
      // Fallback — простая карта
      const fallbackHtml = `
        <!DOCTYPE html>
        <html><head><title>Резервная карта</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
          body, html, #map { height: 100%; width: 100%; margin: 0; padding: 0; }
          .leaflet-control-attribution, .leaflet-control-scale, .leaflet-control-zoom, .leaflet-control-layers { display: none !important; }
        </style>
        </head><body>
        <div id="map"></div>
        <script>
          var map = L.map('map').setView([47.23, 39.71], 11);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '' }).addTo(map);
          L.marker([47.23, 39.71]).addTo(map).bindPopup('Старт');
          ${transformedPoints.map((p, i) => `L.marker([${p.lat}, ${p.lng}]).addTo(map).bindPopup('${i+1}. ${p.address}');`).join('\n')}
          var route = [[47.23, 39.71]];
          ${transformedPoints.map(p => `route.push([${p.lat}, ${p.lng}]);`).join('\n')}
          L.polyline(route, {color: 'blue', weight: 4}).addTo(map);
          map.fitBounds(route);
        </script></body></html>
      `;
      setMapHtml(fallbackHtml);
    } finally {
      setLoading(false);
    }
  }, [points, transformedPoints]);

  useEffect(() => {
    fetchMap();
  }, [fetchMap]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback((event) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      setOrder((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }, []);

  const handleSave = () => {
    onSave(order);
  };

  const handleReset = () => {
    setOrder(transformedPoints);
  };

  const openInYandexMaps = () => {
    if (order.length < 2) {
      alert('Нужно минимум 2 точки для маршрута!');
      return;
    }
    const rtext = order.map(point => `${point.lat},${point.lng}`).join('~');
    window.open(`https://yandex.ru/maps/?rtext=${rtext}&rtt=auto&rtr=driving`, '_blank');
  };

  // === УБИРАЕМ ПОДПИСЬ В IFRAME ===
  const handleIframeLoad = (e) => {
    console.log('Iframe загружен');
    const iframe = e.target;
    const doc = iframe.contentDocument || iframe.contentWindow.document;

    // Вставляем CSS для скрытия подписи и контроллов
    const style = doc.createElement('style');
    style.textContent = `
      .leaflet-control-attribution,
      .leaflet-control-scale,
      .leaflet-control-zoom,
      .leaflet-control-layers,
      .leaflet-control {
        display: none !important;
      }
      .leaflet-container {
        background: #f8f9fa !important;
      }
    `;
    doc.head.appendChild(style);
  };

  return (
    <div className="route-editor">
      <h3>Редактор маршрута по дорогам</h3>
      
      <div style={{ height: '400px', width: '100%', border: '1px solid #ddd', borderRadius: '4px', overflow: 'hidden' }}>
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', backgroundColor: '#f0f0f0' }}>
            <p>Генерация карты... (10-15 сек)</p>
            <p style={{ fontSize: '12px', color: '#666' }}>Не обновляйте страницу</p>
          </div>
        )}
        {error && !loading && (
          <div style={{ padding: '20px', color: 'red', textAlign: 'center', backgroundColor: '#fff5f5' }}>
            <p>{error}</p>
            <button onClick={fetchMap} disabled={loading} style={{ marginTop: '10px', padding: '8px 16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
              Обновить (ждите 10с)
            </button>
          </div>
        )}
        {mapHtml && !loading && (
          <iframe
            srcDoc={mapHtml}
            style={{ height: '100%', width: '100%', border: 'none' }}
            title="Route Map"
            sandbox="allow-scripts allow-same-origin"
            onLoad={handleIframeLoad}
            onError={(e) => console.error('Iframe error:', e)}
          />
        )}
        {points.length === 0 && !loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
            Добавьте точки
          </div>
        )}
      </div>

      <div className="points-list">
        <h4>Порядок (drag & drop):</h4>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={order.map(p => p.id)} strategy={verticalListSortingStrategy}>
            <ul style={{ listStyle: 'none', padding: 0, maxHeight: '200px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
              {order.map((point, index) => (
                <SortableItem key={point.id} id={point.id} index={index} address={point.address} />
              ))}
            </ul>
          </SortableContext>
        </DndContext>
      </div>

      <div className="buttons" style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
        <button onClick={handleSave}>Сохранить</button>
        <button onClick={handleReset}>Сбросить</button>
        <button onClick={openInYandexMaps}>Yandex Maps</button>
        <button onClick={fetchMap} disabled={loading}>Обновить карту</button>
      </div>
    </div>
  );
};

export default RouteEditor;