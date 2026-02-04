import { useState } from 'react';
import { regenerateCell, regenerateAll } from '../api/guides';
import './GuideDisplay.css';

export default function GuideDisplay({ guide, onUpdate }) {
    const [expandedCell, setExpandedCell] = useState(null);
    const [regeneratingCell, setRegeneratingCell] = useState(null);
    const [regeneratingAll, setRegeneratingAll] = useState(false);
    const [feedbackModal, setFeedbackModal] = useState(null);
    const [feedback, setFeedback] = useState('');
    const [globalFeedback, setGlobalFeedback] = useState('');
    const [showGlobalFeedback, setShowGlobalFeedback] = useState(false);

    if (!guide || !guide.guides_examples) {
        return null;
    }

    const { levels, rows } = guide.guides_examples;

    const toggleCell = (competency, level, e) => {
        e.stopPropagation();
        const key = `${competency}-${level}`;
        setExpandedCell(expandedCell === key ? null : key);
    };

    const handleRegenerateCell = async () => {
        if (!feedbackModal) return;

        const { competency, level } = feedbackModal;
        setRegeneratingCell(`${competency}-${level}`);
        setFeedbackModal(null);

        try {
            const response = await regenerateCell(guide.id, competency, level, feedback);

            // Update guide with new examples
            if (onUpdate) {
                const updatedExamples = { ...guide.guides_examples };
                for (const row of updatedExamples.rows) {
                    if (row.competency === competency) {
                        row.cells[level].examples = response.data.examples;
                        row.cells[level].status = 'complete';
                    }
                }
                onUpdate({ ...guide, guides_examples: updatedExamples });
            }
        } catch (err) {
            console.error('Regenerate failed:', err);
        } finally {
            setRegeneratingCell(null);
            setFeedback('');
        }
    };

    const handleRegenerateAll = async () => {
        setRegeneratingAll(true);
        setShowGlobalFeedback(false);

        try {
            const response = await regenerateAll(guide.id, globalFeedback);
            if (onUpdate) {
                onUpdate({ ...guide, guides_examples: response.data.guides_examples });
            }
        } catch (err) {
            console.error('Regenerate all failed:', err);
        } finally {
            setRegeneratingAll(false);
            setGlobalFeedback('');
        }
    };

    const openRegenerateModal = (competency, level, e) => {
        e.stopPropagation();
        setFeedback('');
        setFeedbackModal({ competency, level });
    };

    return (
        <div className="guide-display">
            <div className="guide-header">
                <div className="guide-title">
                    <h2>Levelling Guide v{guide.version}</h2>
                    <span className="guide-meta">
                        {guide.file_name} • {new Date(guide.created_at).toLocaleDateString()}
                    </span>
                </div>
                <button
                    className="btn-regenerate-all"
                    onClick={() => setShowGlobalFeedback(true)}
                    disabled={regeneratingAll}
                >
                    {regeneratingAll ? (
                        <><span className="spinner"></span> Regenerating...</>
                    ) : (
                        <>🔄 Regenerate All</>
                    )}
                </button>
            </div>

            <div className="guide-table-container">
                <table className="guide-table">
                    <thead>
                        <tr>
                            <th className="competency-header">Competency</th>
                            {levels.map((level) => (
                                <th key={level} className="level-header">{level}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row) => (
                            <tr key={row.competency}>
                                <td className="competency-name">{row.competency}</td>
                                {levels.map((level) => {
                                    const cell = row.cells[level];
                                    const key = `${row.competency}-${level}`;
                                    const isExpanded = expandedCell === key;
                                    const isLoading = regeneratingCell === key || cell?.status === 'pending';

                                    return (
                                        <td
                                            key={level}
                                            className={`cell ${isExpanded ? 'expanded' : ''} ${isLoading ? 'loading' : ''}`}
                                            onClick={(e) => toggleCell(row.competency, level, e)}
                                        >
                                            <div className="cell-content">
                                                {isLoading ? (
                                                    <div className="cell-loader">
                                                        <div className="cell-spinner"></div>
                                                        <span>Generating...</span>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <div className="description">{cell?.description || 'N/A'}</div>

                                                        {cell?.examples && cell.examples.length > 0 && (
                                                            <div className={`examples ${isExpanded ? 'show' : ''}`}>
                                                                <div className="examples-header">
                                                                    <span>💡 Examples</span>
                                                                    <button
                                                                        className="btn-regen-cell"
                                                                        onClick={(e) => openRegenerateModal(row.competency, level, e)}
                                                                    >
                                                                        🔄
                                                                    </button>
                                                                </div>
                                                                <ul className="examples-list">
                                                                    {cell.examples.map((example, i) => (
                                                                        <li key={i}>{example}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}

                                                        {cell?.examples && cell.examples.length > 0 && !isExpanded && (
                                                            <div className="expand-hint">
                                                                Click to see {cell.examples.length} examples
                                                            </div>
                                                        )}
                                                    </>
                                                )}
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Regenerate Cell Modal */}
            {feedbackModal && (
                <div className="modal-overlay" onClick={() => setFeedbackModal(null)}>
                    <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
                        <h3>Regenerate Cell</h3>
                        <p>
                            <strong>{feedbackModal.competency}</strong> → {feedbackModal.level}
                        </p>
                        <textarea
                            placeholder="Optional: Add feedback to improve the examples (e.g., 'make them more technical', 'include metrics')..."
                            value={feedback}
                            onChange={(e) => setFeedback(e.target.value)}
                            rows={3}
                        />
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setFeedbackModal(null)}>
                                Cancel
                            </button>
                            <button className="btn-regen" onClick={handleRegenerateCell}>
                                Regenerate
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Global Feedback Modal */}
            {showGlobalFeedback && (
                <div className="modal-overlay" onClick={() => setShowGlobalFeedback(false)}>
                    <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
                        <h3>Regenerate All Examples</h3>
                        <p>This will regenerate examples for all cells.</p>
                        <textarea
                            placeholder="Optional: Add global feedback for all cells (e.g., 'focus on software engineering context', 'make examples shorter')..."
                            value={globalFeedback}
                            onChange={(e) => setGlobalFeedback(e.target.value)}
                            rows={3}
                        />
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => setShowGlobalFeedback(false)}>
                                Cancel
                            </button>
                            <button className="btn-regen" onClick={handleRegenerateAll}>
                                Regenerate All
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
