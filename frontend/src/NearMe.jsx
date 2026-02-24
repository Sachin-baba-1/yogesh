import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { MapPin, ShieldAlert, ShieldCheck, Navigation } from 'lucide-react';

export default function NearMe() {
    const [locations, setLocations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [userCoords, setUserCoords] = useState(null);

    const fetchNearby = async () => {
        setLoading(true);
        setError(null);

        if (!navigator.geolocation) {
            setError('Geolocation is not supported by your browser.');
            setLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                setUserCoords({ lat, lon });

                try {
                    // Query backend for 10km radius (10000 meters approx degrees mapping handled in backend)
                    // Currently backend radius logic is simplified, let's pass an arbitrarily larger radius to simulate 10km
                    const res = await axios.get(`http://localhost:8000/api/location/score?lat=${lat}&lon=${lon}&radius=500000`);

                    // Sort locations by safety score ascending (show most dangerous first)
                    const sorted = (res.data.locations || []).sort((a, b) => a.safety_score - b.safety_score);
                    setLocations(sorted);
                } catch (err) {
                    console.error("Failed to fetch nearby locations", err);
                    setError("Failed to fetch safety data. Is the backend running?");
                } finally {
                    setLoading(false);
                }
            },
            () => {
                setError('Unable to retrieve your location. Please allow location access in your browser.');
                setLoading(false);
            }
        );
    };

    // Auto prompt on component mount
    useEffect(() => {
        fetchNearby();
    }, []);

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--primary-color)' }}>
                        <Navigation /> What's Around Me?
                    </h2>
                    <button onClick={fetchNearby} className="btn btn-primary" disabled={loading}>
                        {loading ? 'Scanning...' : 'Rescan Area'}
                    </button>
                </div>

                <p style={{ color: 'var(--text-muted)' }}>
                    Allow location access so we can scan the area around you for real-time safety scores and potential threats mapped from social discussions.
                </p>

                {error && <div style={{ marginTop: '1rem', color: 'var(--danger)', background: 'rgba(255,0,0,0.1)', padding: '1rem', borderRadius: '8px' }}>{error}</div>}

                {userCoords && !loading && (
                    <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                        <MapPin size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                        Sourced localized data from GPS: {userCoords.lat.toFixed(4)}, {userCoords.lon.toFixed(4)}
                    </div>
                )}
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
                    <Navigation size={40} style={{ animation: 'spin 2s linear infinite', margin: '0 auto', display: 'block' }} />
                    <p style={{ marginTop: '1rem' }}>Sourcing local intelligence...</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gap: '1rem' }}>
                    {locations.length === 0 && userCoords && !loading ? (
                        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                            No active intelligence logged within your immediate vicinity.
                        </div>
                    ) : (
                        locations.map((loc, i) => (
                            <div key={i} className="glass-panel" style={{
                                padding: '1.5rem',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                animation: `fadeIn 0.5s ease ${i * 0.1}s`,
                                animationFillMode: 'both',
                                borderLeft: `4px solid ${loc.safety_score > 60 ? 'var(--safe)' : loc.safety_score > 40 ? 'var(--warning)' : 'var(--danger)'}`
                            }}>
                                <div>
                                    <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        {loc.name}
                                    </h3>
                                    <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                        Last updated: {new Date(loc.last_updated).toLocaleString()}
                                    </div>
                                </div>

                                <div style={{
                                    padding: '0.5rem 1rem',
                                    borderRadius: '20px',
                                    background: 'rgba(0,0,0,0.3)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    fontWeight: 'bold',
                                    color: loc.safety_score > 60 ? 'var(--safe)' : loc.safety_score > 40 ? 'var(--warning)' : 'var(--danger)'
                                }}>
                                    {loc.safety_score > 50 ? <ShieldCheck size={18} /> : <ShieldAlert size={18} />}
                                    Score: {loc.safety_score}/100
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
