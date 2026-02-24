import React, { useState } from 'react';
import axios from 'axios';
import { Link, ShieldAlert, ShieldCheck, FileSearch } from 'lucide-react';

export default function LinkAnalyzer() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleAnalyze = async (e) => {
        e.preventDefault();
        if (!url) return;

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const res = await axios.post('http://localhost:8000/api/analyze-url', { url });
            setResult(res.data);
        } catch (err) {
            setError("Failed to analyze link. Make sure the backend is running.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--primary-color)' }}>
                    <FileSearch /> Analyze Social Post
                </h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                    Paste a Twitter, Instagram, or any social media link below. Our AI will automatically scan the post and comments for safety concerns and extract named locations.
                </p>

                <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Link style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} size={20} />
                        <input
                            type="url"
                            className="input-field"
                            placeholder="https://twitter.com/..."
                            style={{ paddingLeft: '3rem' }}
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? "Analyzing..." : "Analyze Link"}
                    </button>
                </form>
                {error && <p style={{ color: 'var(--danger)', marginTop: '1rem' }}>{error}</p>}
            </div>

            {result && (
                <div className="glass-panel" style={{ padding: '2rem', animation: 'fadeIn 0.5s ease' }}>
                    <h3 style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                        Analysis Results
                    </h3>

                    <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
                        <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Overall Classification</div>
                            <div style={{
                                fontSize: '1.5rem',
                                fontWeight: 'bold',
                                color: result.post.severity > 0.5 ? 'var(--danger)' : 'var(--safe)',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}>
                                {result.post.severity > 0.5 ? <ShieldAlert /> : <ShieldCheck />}
                                {result.post.classification.replace('_', ' ').toUpperCase()}
                            </div>
                        </div>

                        <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Extracted Location Risks</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                                {result.location_summary.safety_score} / 100
                            </div>
                            <div style={{ color: 'var(--warning)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                                Trend: {result.location_summary.trend}
                            </div>
                        </div>
                    </div>

                    <h4 style={{ marginBottom: '1rem', color: 'var(--text-muted)' }}>Analyzed Content</h4>
                    <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', fontStyle: 'italic', borderLeft: '4px solid var(--primary-color)' }}>
                        "{result.post.text}"
                    </div>

                    {result.post.locations && result.post.locations.length > 0 && (
                        <div style={{ marginTop: '2rem' }}>
                            <h4 style={{ marginBottom: '1rem', color: 'var(--text-muted)' }}>Geographic Extraction (NER)</h4>
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                {result.post.locations.map((loc, idx) => (
                                    <li key={idx} style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        padding: '0.75rem',
                                        background: 'rgba(0,0,0,0.2)',
                                        marginBottom: '0.5rem',
                                        borderRadius: '8px'
                                    }}>
                                        <span><strong>{loc.name}</strong></span>
                                        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                            Confidence: {(loc.confidence * 100).toFixed(0)}%
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
