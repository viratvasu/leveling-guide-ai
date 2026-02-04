import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
    uploadGuide,
    generateGuideExamples,
    getCurrentGuide,
    listGuides,
    getGuide,
    setCurrentVersion
} from '../api/guides';
import UploadModal from '../components/UploadModal';
import GuideDisplay from '../components/GuideDisplay';
import MyCareerPath from '../components/MyCareerPath';
import './LevellingGuide.css';

export default function LevellingGuide() {
    const { canConfigure, currentRole, user } = useAuth();
    const [guide, setGuide] = useState(null);
    const [allGuides, setAllGuides] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showConfigureView, setShowConfigureView] = useState(false);
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState('');

    const hasConfigurePermission = canConfigure('levelling_guide');
    const userLevel = user?.current_role || currentRole || '';

    useEffect(() => {
        fetchGuides();
    }, []);

    const fetchGuides = async () => {
        try {
            setLoading(true);
            const response = await getCurrentGuide();
            setGuide(response.data?.guide || null);

            // If user can configure, also fetch all versions
            if (hasConfigurePermission) {
                const listResponse = await listGuides();
                setAllGuides(listResponse.data?.guides || []);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenConfigure = () => {
        setShowConfigureView(true);
    };

    const handleBackToCareerPath = () => {
        setShowConfigureView(false);
    };

    const handleSelectVersion = async (guideId) => {
        try {
            setLoading(true);
            const response = await getGuide(guideId);
            setGuide(response.data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSetCurrent = async (guideId) => {
        try {
            await setCurrentVersion(guideId);
            const listResponse = await listGuides();
            setAllGuides(listResponse.data?.guides || []);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleUpload = async (file, companyWebsite) => {
        try {
            setUploading(true);
            setError('');

            const uploadResponse = await uploadGuide(file, companyWebsite);
            const newGuideId = uploadResponse.data.id;

            setShowUploadModal(false);
            setGuide({
                id: newGuideId,
                version: uploadResponse.data.version,
                file_name: uploadResponse.data.file_name,
                created_at: new Date().toISOString(),
                status: 'pending',
                guides_examples: uploadResponse.data.guides_examples,
            });

            setAllGuides(prev => [{
                id: newGuideId,
                version: uploadResponse.data.version,
                file_name: uploadResponse.data.file_name,
                created_at: new Date().toISOString(),
                is_current_version: true,
                status: 'pending'
            }, ...prev.map(g => ({ ...g, is_current_version: false }))]);

            setGenerating(true);
            const genResponse = await generateGuideExamples(newGuideId);

            setGuide(prev => ({
                ...prev,
                status: 'complete',
                guides_examples: genResponse.data.guides_examples,
            }));

        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
            setGenerating(false);
        }
    };

    const handleGuideUpdate = (updatedGuide) => {
        setGuide(updatedGuide);
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
            </div>
        );
    }

    // CONFIGURE VIEW - only when user clicks Configure
    if (showConfigureView && hasConfigurePermission) {
        return (
            <div className="levelling-guide-page">
                <div className="page-header">
                    <div className="header-left">
                        <button className="btn-back" onClick={handleBackToCareerPath}>
                            ← Back to My Career Path
                        </button>
                        <h2>Configure Levelling Guide</h2>
                        {allGuides.length > 0 && (
                            <div className="version-selector">
                                <label>Version:</label>
                                <select
                                    value={guide?.id || ''}
                                    onChange={(e) => handleSelectVersion(parseInt(e.target.value))}
                                >
                                    {allGuides.map((g) => (
                                        <option key={g.id} value={g.id}>
                                            v{g.version} {g.is_current_version ? '(Active)' : ''} - {new Date(g.created_at).toLocaleDateString()}
                                        </option>
                                    ))}
                                </select>
                                {guide && !allGuides.find(g => g.id === guide.id)?.is_current_version && (
                                    <button
                                        className="btn-set-current"
                                        onClick={() => handleSetCurrent(guide.id)}
                                    >
                                        Set as Active
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    <button
                        onClick={() => setShowUploadModal(true)}
                        className="upload-btn"
                        disabled={generating}
                    >
                        {generating ? (
                            <><span className="spinner"></span> Generating...</>
                        ) : (
                            <><span>📤</span> Upload New Version</>
                        )}
                    </button>
                </div>

                {error && (
                    <div className="error-banner">
                        <span>⚠</span> {error}
                        <button onClick={() => setError('')}>×</button>
                    </div>
                )}

                {generating && (
                    <div className="generating-banner">
                        <span className="spinner"></span>
                        Generating AI examples for all cells... This may take 15-30 seconds.
                    </div>
                )}

                {guide ? (
                    <GuideDisplay guide={guide} onUpdate={handleGuideUpdate} />
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">📊</div>
                        <h3>No Levelling Guides Yet</h3>
                        <p>Upload a CSV file to get started with AI-generated examples.</p>
                    </div>
                )}

                {showUploadModal && (
                    <UploadModal
                        onClose={() => !uploading && setShowUploadModal(false)}
                        onUpload={handleUpload}
                        isUploading={uploading}
                    />
                )}
            </div>
        );
    }

    // DEFAULT VIEW - Everyone sees their career path (read-only)
    return (
        <div className="levelling-guide-page">
            {error && (
                <div className="error-banner">
                    <span>⚠</span> {error}
                    <button onClick={() => setError('')}>×</button>
                </div>
            )}

            <MyCareerPath
                guide={guide}
                userCurrentRole={userLevel}
                canConfigure={hasConfigurePermission}
                onOpenConfigure={handleOpenConfigure}
            />
        </div>
    );
}
