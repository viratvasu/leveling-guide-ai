import { useState, useEffect } from 'react';
import './MyCareerPath.css';

export default function MyCareerPath({ guide, userCurrentRole, onOpenConfigure, canConfigure }) {
    const [selectedLevel, setSelectedLevel] = useState(null);

    // No guide available
    if (!guide || !guide.guides_examples) {
        return (
            <div className="career-page">
                <div className="career-header">
                    <div>
                        <h1>My Career Path</h1>
                        <p className="subtitle">
                            Map your professional growth and understand what's expected at each level.
                        </p>
                    </div>
                    {canConfigure && (
                        <button className="btn-settings" onClick={onOpenConfigure}>
                            ⚙️ Configure
                        </button>
                    )}
                </div>
                <div className="career-empty">
                    <h3>📊 No Levelling Guide Available</h3>
                    <p>Your company hasn't set up a levelling guide yet.</p>
                </div>
            </div>
        );
    }

    const { levels, rows } = guide.guides_examples;
    const currentLevelIndex = levels.findIndex(level => level === userCurrentRole);

    const currentIdx = currentLevelIndex;
    const activeIdx = selectedLevel !== null ? selectedLevel : currentIdx;
    const activeLevel = levels[activeIdx];
    const nextIdx = activeIdx + 1 < levels.length ? activeIdx + 1 : null;

    return (
        <div className="career-page">
            {/* Header - Always Visible */}
            <div className="career-header">
                <div>
                    <h1>My Career Path</h1>
                    <p className="subtitle">
                        Map your professional growth and understand what's expected at each level.
                    </p>
                </div>
                {canConfigure && (
                    <button className="btn-settings" onClick={onOpenConfigure} title="Configure Guide">
                        ⚙️ Configure
                    </button>
                )}
            </div>

            {/* Error State: Level Not Found */}
            {currentLevelIndex === -1 ? (
                <div className="career-error">
                    <h3>⚠️ Level Not Found</h3>
                    <p>Your role "<strong>{userCurrentRole || 'Unknown'}</strong>" doesn't match any level in the guide.</p>
                    <p className="hint">Please contact your admin team.</p>
                </div>
            ) : (
                /* Main Content */
                <>
                    <div className="milestone-slider">
                        <div className="milestone-track">
                            {levels.map((level, i) => {
                                const isPast = i < currentIdx;
                                const isCurrent = i === currentIdx;
                                const isFuture = i > currentIdx;
                                const isActive = i === activeIdx;

                                return (
                                    <div
                                        key={level}
                                        className={`milestone ${isPast ? 'past' : ''} ${isCurrent ? 'current' : ''} ${isFuture ? 'future' : ''} ${isActive ? 'active' : ''}`}
                                        onClick={() => setSelectedLevel(i)}
                                    >
                                        <div className="milestone-dot">
                                            {isCurrent && <span className="you-badge">YOU</span>}
                                        </div>
                                        <div className="milestone-label">{level.replace('Software Engineer', 'SWE')}</div>
                                    </div>
                                );
                            })}
                        </div>
                        <div className="milestone-line"></div>
                    </div>

                    <div className="level-details">
                        <div className="level-card main">
                            <div className="level-card-header">
                                <span className="level-name">{activeLevel}</span>
                                {activeIdx === currentIdx && <span className="tag current">Current Level</span>}
                                {activeIdx === currentIdx + 1 && <span className="tag next">Next Level</span>}
                            </div>

                            <div className="competencies-list">
                                {rows.map((row) => {
                                    const cell = row.cells[activeLevel];
                                    return (
                                        <div key={row.competency} className="competency-item">
                                            <h4>{row.competency}</h4>
                                            <p className="description">{cell?.description || 'No description'}</p>
                                            {cell?.examples && cell.examples.length > 0 && (
                                                <div className="career-examples">
                                                    <span className="career-examples-label">💡 Examples:</span>
                                                    <ul>
                                                        {cell.examples.map((ex, i) => (
                                                            <li key={i}>{ex}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Quick peek at next level */}
                        {nextIdx !== null && (
                            <div className="next-peek">
                                <button
                                    className="peek-btn"
                                    onClick={() => setSelectedLevel(nextIdx)}
                                >
                                    👉 See what's next: <strong>{levels[nextIdx]}</strong>
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
