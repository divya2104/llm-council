import './JdGeneratedPanel.css';

export default function JdGeneratedPanel({ draft, activeTab, onSelectTab, onBackToDashboard, children }) {
  return (
    <div className="jd-generated-panel">
      <div className="jd-generated-banner">
        {draft.generated_result?.message || 'JD generation coming soon.'}
      </div>

      <div className="jd-detail-toggle">
        <button className="jd-lob-back" onClick={onBackToDashboard}>
          ← Back to {draft.lob} JDs
        </button>
        <span className="jd-detail-toggle-spacer" />
        <button
          className={`jd-detail-tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => onSelectTab('editor')}
        >
          JD Editor
        </button>
        <button
          className={`jd-detail-tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => onSelectTab('chat')}
        >
          Council Chat
        </button>
      </div>

      <div className="jd-generated-content">{children}</div>
    </div>
  );
}
