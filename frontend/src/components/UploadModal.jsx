import { useState, useRef } from 'react';
import './UploadModal.css';

export default function UploadModal({ onClose, onUpload, onCancel, isUploading }) {
    const [step, setStep] = useState('upload'); // 'upload' | 'preview' | 'confirm'
    const [file, setFile] = useState(null);
    const [companyWebsite, setCompanyWebsite] = useState('');
    const [preview, setPreview] = useState(null);
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    const parseCSVPreview = (content) => {
        const lines = content.split('\n').filter(line => line.trim());
        const rows = lines.map(line => {
            const result = [];
            let current = '';
            let inQuotes = false;

            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                if (char === '"') {
                    inQuotes = !inQuotes;
                } else if (char === ',' && !inQuotes) {
                    result.push(current.trim().replace(/\n/g, ' '));
                    current = '';
                } else {
                    current += char;
                }
            }
            result.push(current.trim().replace(/\n/g, ' '));
            return result;
        });

        return {
            headers: rows[0] || [],
            data: rows.slice(1),
        };
    };

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        setError('');

        if (!selectedFile) {
            setFile(null);
            setPreview(null);
            return;
        }

        if (!selectedFile.name.endsWith('.csv')) {
            setError('Please select a CSV file');
            return;
        }

        if (selectedFile.size > 1024 * 1024) {
            setError('File size must be less than 1MB');
            return;
        }

        setFile(selectedFile);

        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target.result;
            const parsed = parseCSVPreview(content);
            setPreview(parsed);
            setStep('preview'); // Auto-advance to preview
        };
        reader.readAsText(selectedFile);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            handleFileChange({ target: { files: [droppedFile] } });
        }
    };

    const handleBack = () => {
        if (step === 'preview') {
            setStep('upload');
        } else if (step === 'confirm') {
            setStep('preview');
        }
    };

    const handleConfirmGenerate = () => {
        setStep('confirm');
    };

    const handleGenerate = () => {
        if (!file) return;
        onUpload(file, companyWebsite);
    };

    // Step 1: Upload
    if (step === 'upload') {
        return (
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                    <div className="modal-header">
                        <h2>Upload Levelling Guide</h2>
                        <button className="close-btn" onClick={onClose}>×</button>
                    </div>

                    <div className="modal-body">
                        {error && <div className="error-msg"><span>⚠</span> {error}</div>}

                        <div className="form-group">
                            <label>Company Website (optional)</label>
                            <input
                                type="url"
                                value={companyWebsite}
                                onChange={(e) => setCompanyWebsite(e.target.value)}
                                placeholder="https://example.com"
                            />
                            <span className="help">Provides context for AI-generated examples</span>
                        </div>

                        <div
                            className="drop-zone"
                            onDrop={handleDrop}
                            onDragOver={(e) => e.preventDefault()}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".csv"
                                onChange={handleFileChange}
                                style={{ display: 'none' }}
                            />
                            <div className="drop-icon">📁</div>
                            <p>Drag & drop a CSV file, or click to select</p>
                        </div>
                    </div>

                    <div className="modal-footer">
                        <button className="btn-secondary" onClick={onClose}>Cancel</button>
                    </div>
                </div>
            </div>
        );
    }

    // Step 2: Full Preview
    if (step === 'preview') {
        return (
            <div className="modal-overlay">
                <div className="modal-content modal-fullscreen" onClick={(e) => e.stopPropagation()}>
                    <div className="modal-header">
                        <div className="header-info">
                            <button className="btn-back" onClick={handleBack}>← Back</button>
                            <h2>Preview: {file?.name}</h2>
                            <span className="cell-count">
                                {preview?.data.length} competencies × {(preview?.headers.length || 1) - 1} levels
                            </span>
                        </div>
                        <button className="close-btn" onClick={onClose}>×</button>
                    </div>

                    <div className="modal-body preview-body">
                        <table className="preview-table">
                            <thead>
                                <tr>
                                    {preview?.headers.map((header, i) => (
                                        <th key={i}>{header || `Column ${i + 1}`}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {preview?.data.map((row, i) => (
                                    <tr key={i}>
                                        {row.map((cell, j) => (
                                            <td key={j}>{cell}</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="modal-footer">
                        <button className="btn-secondary" onClick={handleBack}>
                            ← Back to Upload
                        </button>
                        <button className="btn-primary" onClick={handleConfirmGenerate}>
                            Continue to Generate →
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Step 3: Confirm Generate
    if (step === 'confirm') {
        const totalCells = (preview?.data.length || 0) * ((preview?.headers.length || 1) - 1);

        return (
            <div className="modal-overlay">
                <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                    <div className="modal-header">
                        <h2>Generate AI Examples?</h2>
                        <button className="close-btn" onClick={onClose}>×</button>
                    </div>

                    <div className="modal-body confirm-body">
                        <div className="confirm-icon">🤖</div>
                        <h3>Ready to Generate</h3>
                        <p>
                            We'll use AI to generate 3 real-world examples for each cell in your leveling guide.
                        </p>

                        <div className="confirm-stats">
                            <div className="stat">
                                <span className="stat-value">{totalCells}</span>
                                <span className="stat-label">Cells to process</span>
                            </div>
                            <div className="stat">
                                <span className="stat-value">~{Math.ceil(totalCells * 0.5)}s</span>
                                <span className="stat-label">Estimated time</span>
                            </div>
                        </div>

                        <p className="confirm-note">
                            You can regenerate individual cells or all cells after generation.
                        </p>
                    </div>

                    <div className="modal-footer">
                        <button className="btn-secondary" onClick={handleBack} disabled={isUploading}>
                            ← Back to Preview
                        </button>
                        <button
                            className="btn-primary btn-generate"
                            onClick={handleGenerate}
                            disabled={isUploading}
                        >
                            {isUploading ? (
                                <><span className="spinner"></span> Generating...</>
                            ) : (
                                <>🚀 Generate Examples</>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return null;
}
