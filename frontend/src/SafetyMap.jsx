import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, Popup, useMap } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import { AlertTriangle, Info } from 'lucide-react';

// Default to center of India (Nagpur)
const DEFAULT_CENTER = [21.1458, 79.0882];

function ChangeView({ center, zoom }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

export default function SafetyMap() {
  const [locations, setLocations] = useState([]);
  const [center, setCenter] = useState(DEFAULT_CENTER);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app we'd fetch bounds based on map pan.
    // For MVP, fetch a wide radius across India
    fetchScores(center[0], center[1]);
  }, []);

  const fetchScores = async (lat, lon) => {
    setLoading(true);
    try {
      // Calling our Django Backend
      const res = await axios.get(`http://localhost:8000/api/location/score?lat=${lat}&lon=${lon}&radius=2000000`); // very wide radius to fetch national points
      setLocations(res.data.locations || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getZoneProperties = (score) => {
    // Return Color and Radius based on severity
    if (score >= 80) return { color: 'var(--safe)', radius: 3000 }; // 3km small safe zone
    if (score >= 50) return { color: 'var(--warning)', radius: 6000 }; // 6km warning zone
    return { color: 'var(--danger)', radius: 10000 }; // 10km large danger zone
  };

  return (
    <div className="glass-panel" style={{ height: 'calc(100vh - 8rem)', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle color="var(--primary-color)" /> Live Safety Map (India)
        </h2>
        {loading && <span style={{ color: 'var(--text-muted)' }}>Updating sensors...</span>}
      </div>

      <div style={{ flex: 1, borderRadius: '12px', overflow: 'hidden' }}>
        <MapContainer center={center} zoom={5} style={{ height: '100%', width: '100%' }}>
          <ChangeView center={center} zoom={5} />

          {/* Dark map tiles matching the glassmorphism theme */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
          />

          {locations.map((loc, i) => {
            // center of box
            const locLat = (loc.min_lat + loc.max_lat) / 2;
            const locLon = (loc.min_lon + loc.max_lon) / 2;
            const zone = getZoneProperties(loc.safety_score);

            return (
              <Circle
                key={i}
                center={[locLat, locLon]}
                radius={zone.radius}
                pathOptions={{
                  fillColor: zone.color,
                  fillOpacity: 0.35,
                  color: zone.color,
                  weight: 2
                }}
              >
                <Popup className="custom-popup">
                  <div style={{ color: '#333', padding: '0.25rem' }}>
                    <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
                      {loc.name}
                    </h3>
                    <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(0,0,0,0.05)', marginBottom: '0.5rem' }}>
                      <p style={{ margin: 0, fontWeight: 'bold', color: zone.color, display: 'flex', justifyContent: 'space-between' }}>
                        <span>Status:</span>
                        <span>{loc.safety_score >= 80 ? 'SAFE' : loc.safety_score >= 50 ? 'MODERATE' : 'UNSAFE'}</span>
                      </p>
                    </div>
                    <p style={{ margin: 0, fontWeight: 'bold' }}>
                      Safety Score: {loc.safety_score} / 100
                    </p>
                  </div>
                </Popup>
              </Circle>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
