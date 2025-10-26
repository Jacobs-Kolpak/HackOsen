import React, { useState, useEffect, useCallback, useRef } from 'react';
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

async function getOptimizedRoute() {
  const response = await fetch('/api/jacobs/routing/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  if (!response.ok) throw new Error('Failed to optimize');
  return response.json();
}

function SortableItem({ id, index, address, onDelete }) {
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
  const [isOptimized, setIsOptimized] = useState(true);
  const [autoFetch, setAutoFetch] = useState(false);

  const orderRef = useRef(order);
  const isOptimizedRef = useRef(isOptimized);

  useEffect(() => {
    orderRef.current = order;
  }, [order]);

  useEffect(() => {
    isOptimizedRef.current = isOptimized;
  }, [isOptimized]);

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
    setAutoFetch(true);
  }, [transformedPoints]);

  const generateFallbackHtml = useCallback(() => {
    const currentOrder = orderRef.current;
    const addresses = currentOrder.map(p => p.address);
    return `
      <!DOCTYPE html>
      <html>
      <head>
      <title>Резервная карта</title>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <script src="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js"></script>
      <style>
        body, html, #map { height: 100%; width: 100%; margin: 0; padding: 0; }
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
      </style>
      </head>
      <body>
      <div id="map"></div>
      <script>
        var map = L.map('map', {attributionControl: false, zoomControl: false});
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var start = L.latLng(47.23, 39.71);
        var waypoints = [start];
        ${currentOrder.map((p) => `waypoints.push(L.latLng(${p.lat}, ${p.lng}));`).join('\n')}
        var addresses = ${JSON.stringify(addresses)};
        L.Routing.control({
          waypoints: waypoints,
          router: L.Routing.osrmv1({serviceUrl: 'https://router.project-osrm.org/route/v1'}),
          lineOptions: {styles: [{color: 'blue', opacity: 0.6, weight: 4}]},
          addWaypoints: false,
          draggableWaypoints: false,
          fitSelectedRoutes: true,
          show: false,
          createMarker: function(i, waypoint, n) {
            var marker = L.marker(waypoint.latLng);
            var label = (i === 0) ? 'Старт' : '' + i + '. ' + addresses[i-1];
            marker.bindPopup(label);
            return marker;
          }
        }).addTo(map);
      </script>
      </body>
      </html>
    `;
  }, []);

  const fetchMap = useCallback(async () => {
    if (orderRef.current.length === 0) {
      setMapHtml('');
      setError('');
      setLoading(false);
      return;
    }

    if (loading) {
      return;
    }

    try {
      setLoading(true);
      setError('');
      let html;
      if (isOptimizedRef.current) {
        console.log('Генерация оптимизированной карты... (10-15 сек)');
        html = await getOptimizedMap();
      } else {
        console.log('Генерация пользовательской карты...');
        html = generateFallbackHtml();
      }
      setMapHtml(html);
    } catch (err) {
      console.error('Ошибка загрузки карты:', err);
      setError(err.message || 'Неизвестная ошибка');
      const fallbackHtml = generateFallbackHtml();
      setMapHtml(fallbackHtml);
    } finally {
      setLoading(false);
    }
  }, [loading, generateFallbackHtml]);

  useEffect(() => {
    if (autoFetch) {
      setAutoFetch(false);
      fetchMap();
    }
  }, [autoFetch, fetchMap]);

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
      setIsOptimized(false);
      setAutoFetch(true);
    }
  }, []);

  const handleDelete = useCallback((id) => {
    setOrder((prev) => prev.filter((item) => item.id !== id));
    setIsOptimized(false);
    setAutoFetch(true);
  }, []);

  const handleOptimize = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      console.log('Оптимизация маршрута... (10-15 сек)');
      const data = await getOptimizedRoute();
      if (data.success) {
        const newOrder = data.route_points.map((point) => ({
          id: point.object_number,
          lat: point.latitude,
          lng: point.longitude,
          address: point.address,
        }));
        setOrder(newOrder);
        setIsOptimized(true);
        setAutoFetch(true);
      } else {
        setError(data.message || 'Ошибка оптимизации');
      }
    } catch (err) {
      console.error('Ошибка оптимизации:', err);
      setError(err.message || 'Неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSave = () => {
    onSave(order);
  };

  const handleReset = () => {
    setOrder(transformedPoints);
    setIsOptimized(true);
    setAutoFetch(true);
  };

  const openInYandexMaps = () => {
    if (order.length < 2) {
      alert('Нужно минимум 2 точки для маршрута!');
      return;
    }
    const start = [47.23, 39.71];
    const coords = [start, ...order.map(point => [point.lat, point.lng])];
    const rtext = coords.map(([lat, lng]) => `${lat},${lng}`).join('~');
    window.open(`https://yandex.ru/maps/?rtext=${rtext}&rtt=auto&rtr=driving`, '_blank');
  };

  const handleIframeLoad = (e) => {
    console.log('Iframe загружен');
    const iframe = e.target;
    const doc = iframe.contentDocument || iframe.contentWindow.document;

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
        <h4>Порядок:</h4>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={order.map(p => p.id)} strategy={verticalListSortingStrategy}>
            <ul style={{ listStyle: 'none', padding: 0, maxHeight: '200px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
              {order.map((point, index) => (
                <SortableItem
                  key={point.id}
                  id={point.id}
                  index={index}
                  address={point.address}
                  onDelete={handleDelete}
                />
              ))}
            </ul>
          </SortableContext>
        </DndContext>
      </div>

      <div className="buttons" style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
        <button onClick={handleSave}>Сохранить</button>
        <button onClick={handleReset}>Сбросить</button>
        <button onClick={openInYandexMaps}>Yandex Maps</button>
        <button onClick={handleOptimize} disabled={loading}>Оптимизировать</button>
        <button onClick={fetchMap} disabled={loading}>Обновить карту</button>
      </div>
    </div>
  );
};

export default RouteEditor;