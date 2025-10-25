// RouteEditor.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css';
import 'leaflet-routing-machine';
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
import {
  useSortable,
} from '@dnd-kit/sortable';
// import './RouteEditor.css';
import { CSS } from '@dnd-kit/utilities';
import '../styles/routeeditor.css'


// Фикс иконок Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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
  const [map, setMap] = useState(null);
  const [routingControl, setRoutingControl] = useState(null);

  // Преобразование входящих points в нужный формат {id, lat, lng, address}
  const transformedPoints = React.useMemo(() => {
    return points.map(point => ({
      id: point.object_number || point.id,
      lat: point.latitude || point.lat,
      lng: point.longitude || point.lng,
      address: point.address,
    }));
  }, [points]);

  // Установка начального порядка при изменении points
  useEffect(() => {
    setOrder(transformedPoints);
  }, [transformedPoints]);

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

  // Обновление маршрута
  useEffect(() => {
    if (map && order.length > 1) {
      // Удаляем старый маршрут
      if (routingControl) {
        map.removeControl(routingControl);
      }

      // Создаём новый маршрут
      const newRoutingControl = L.Routing.control({
        waypoints: order.map(point => L.latLng(point.lat, point.lng)),
        routeWhileDragging: true,
        show: false, // Скрываем панель, только линия
        addWaypoints: false,
        createMarker: (i) => L.marker([order[i].lat, order[i].lng], { icon: L.divIcon({ className: 'custom-marker', html: `<div>${i + 1}</div>` }) }),
        lineOptions: { styles: [{ color: 'blue', weight: 4 }] },
      }).addTo(map);

      setRoutingControl(newRoutingControl);
      // Зум на маршрут
      newRoutingControl.on('routesfound', (e) => {
        const bounds = e.routes[0].bounds;
        map.fitBounds(bounds, { padding: [20, 20] });
      });
    }
  }, [order, map, routingControl]);

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

  // Центр на Ростове
  const center = [47.23, 39.71]; // lat, lng Ростов

  return (
    <div className="route-editor">
      <h3>Редактор маршрута по дорогам</h3>
      
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '400px', width: '100%' }}
        whenCreated={setMap}
        attributionControl={false} // ← добавлено!
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {order.map((point, index) => (
          <Marker key={point.id} position={[point.lat, point.lng]}>
            <Popup>{index + 1}. {point.address}</Popup>
          </Marker>
        ))}
      </MapContainer>

      <div className="points-list">
        <h4>Порядок посещения (перетащи):</h4>
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

      <div className="buttons">
        {/* <button onClick={handleSave}>Сохранить</button> */}
        <button onClick={handleReset}>Сбросить</button>
        <button onClick={openInYandexMaps}>Открыть в Yandex Maps</button>
       
      </div>
    </div>
  );
};

export default RouteEditor;