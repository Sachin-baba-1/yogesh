import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, Plus, Trash2, ShieldCheck, ShieldAlert, Activity } from 'lucide-react';

export default function UserCrawler() {
    const [urls, setUrls] = useState([]);
    const [newUrl, setNewUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const API_BASE = 'http://localhost:8000/api/user-url';

    const fetchUrls = async () => {
        try {
            const res = await axios.get(API_BASE);
            setUrls(res.data);
        } catch (err) {
            console.error("Failed to fetch URLs", err);
        }
    };

    useEffect(() => {
        fetchUrls();
    }, []);

    const handleAddUrl = async (e) => {
        e.preventDefault();
        if (!newUrl) return;

        setLoading(true);
        setError(null);

        try {
            await axios.post(API_BASE, { url: newUrl });
            setNewUrl('');
            fetchUrls();
        } catch (err) {
            setError(err.response?.data?.error || "Failed to add URL.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return "Never";
        return new Date(dateString).toLocaleString();
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--primary-color)' }}>
                    <Clock /> 3-Hour Active Monitor
                </h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                    Submit a specific social media profile or link below. Our aggressive background cron job will fetch the latest content from these URLs every 3 hours and update the map automatically.
                </p>

                <form onSubmit={handleAddUrl} style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Plus style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} size={20} />
                        <input
                            type="url"
                            className="input-field"
                            placeholder="https://twitter.com/suspect_profile"
                            style={{ paddingLeft: '3rem' }}
                            value={newUrl}
                            onChange={(e) => setNewUrl(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? "Adding..." : "Add to Monitor"}
                    </button>
                </form>
                {error && <p style={{ color: 'var(--danger)', marginTop: '1rem' }}>{error}</p>}
            </div>

            <h3 style={{ marginBottom: '1rem', color: 'var(--text-light)' }}>Actively Monitored Profiles</h3>

            {urls.length === 0 ? (
                <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No profiles are currently being monitored. Add one above!
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {urls.map((u) => (
                        <div key={u.id} className="glass-panel" style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <div style={{ fontWeight: 'bold', fontSize: '1.1rem', marginBottom: '0.25rem', color: 'var(--primary-color)' }}>
                                    {u.url}
                                </div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', gap: '1.5rem' }}>
                                    <span>Added: {formatDate(u.added_at)}</span>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                        <Activity size={14} color={u.last_crawled ? 'var(--safe)' : 'var(--warning)'} />
                                        Last Crawled: {formatDate(u.last_crawled)}
                                    </span>
                                </div>
                            </div>
                            <div style={{ background: 'rgba(0,255,100,0.1)', color: 'var(--safe)', padding: '0.5rem 1rem', borderRadius: '20px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <ShieldCheck size={16} /> Active
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
