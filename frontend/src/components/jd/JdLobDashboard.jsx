import { useState } from 'react';
import JdConfirmDialog from './JdConfirmDialog';
import './JdLobDashboard.css';

function getInitials(title) {
  const words = title.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return '?';
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 7h16" />
      <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
      <path d="M18 7l-.8 13a1 1 0 0 1-1 1H7.8a1 1 0 0 1-1-1L6 7" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function JdCard({ draft, onSelectDraft, onRequestDelete }) {
  const initials = getInitials(draft.title);
  const badgeClass = draft.lob === 'NBFC' ? 'jd-card-badge-nbfc' : 'jd-card-badge-amc';
  const isDraft = draft.status === 'draft';
  const percent = draft.completion_percent ?? 0;

  const ringCircumference = 2 * Math.PI * 8;
  const ringOffset = ringCircumference - (percent / 100) * ringCircumference;

  return (
    <div
      className={`jd-card ${isDraft ? 'status-draft' : 'status-completed'}`}
      onClick={() => onSelectDraft(draft.id)}
    >
      {isDraft && (
        <div className="jd-card-pill-row">
          <span className="jd-card-pill">
            <svg className="jd-card-pill-ring" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="8" fill="none" stroke="var(--warning-wash)" strokeWidth="3" />
              <circle
                cx="10"
                cy="10"
                r="8"
                fill="none"
                stroke="var(--warning)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={ringCircumference}
                strokeDashoffset={ringOffset}
                transform="rotate(-90 10 10)"
              />
            </svg>
            {percent}% complete
          </span>
        </div>
      )}

      <div className="jd-card-header">
        <span className={`jd-card-badge ${badgeClass}`}>{initials}</span>
        <span className="jd-card-title">{draft.title}</span>
      </div>

      <div className="jd-card-detail">
        <svg className="jd-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <circle cx="12" cy="8" r="3.5" />
          <path d="M4.5 20c1.5-4 4.5-6 7.5-6s6 2 7.5 6" />
        </svg>
        {draft.prepared_by_name ? (
          <span>Prepared by {draft.prepared_by_name}</span>
        ) : (
          <span className="jd-card-detail-muted">Not yet signed off</span>
        )}
      </div>

      <div className="jd-card-detail">
        <svg className="jd-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 7.5V12l3 2" />
        </svg>
        <span>Updated {new Date(draft.updated_at).toLocaleDateString()}</span>
      </div>

      <div className="jd-card-actions">
        {isDraft && (
          <button
            className="jd-card-delete-pill"
            onClick={(e) => {
              e.stopPropagation();
              onRequestDelete(draft);
            }}
            aria-label="Delete this JD"
            title="Delete this JD"
          >
            <TrashIcon />
            Delete
          </button>
        )}
        <button className="jd-card-view-pill" onClick={() => onSelectDraft(draft.id)}>
          View details
          <ArrowRightIcon />
        </button>
      </div>
    </div>
  );
}

function ChevronIcon({ open }) {
  return (
    <svg
      className={`jd-lob-chevron ${open ? 'open' : ''}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3v12M7 10l5 5 5-5" />
      <path d="M4 19h16" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 21V9M7 14l5-5 5 5" />
      <path d="M4 19h16" />
    </svg>
  );
}

function DraftListIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 6h11M4 12h8M4 18h5" />
      <path d="M14.5 19.5L19 15l1.5 1.5-4.5 4.5H14.5v-1.5z" />
    </svg>
  );
}

function CompletedListIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 6H20M9.5 12H20M9.5 18H20" />
      <path d="M4 6l1.3 1.3L7.8 4.8" />
      <path d="M4 12l1.3 1.3 2.5-2.5" />
      <path d="M4 18l1.3 1.3 2.5-2.5" />
    </svg>
  );
}

function JdStatusSection({ title, tone, count, emptyText, drafts, onSelectDraft, onRequestDelete }) {
  const [open, setOpen] = useState(true);
  const Icon = tone === 'draft' ? DraftListIcon : CompletedListIcon;

  return (
    <section className={`jd-lob-section tone-${tone}`}>
      <button className="jd-lob-section-header" onClick={() => setOpen((o) => !o)}>
        <span className="jd-lob-section-title">
          <Icon className={`jd-lob-status-icon ${tone}`} />
          {title}
        </span>
        <span className="jd-lob-section-right">
          <span className={`jd-lob-count ${tone}`}>{count}</span>
          <ChevronIcon open={open} />
        </span>
      </button>

      {open && (
        <div className="jd-lob-section-body">
          {drafts.length === 0 ? (
            <div className="jd-lob-empty">{emptyText}</div>
          ) : (
            <div className="jd-lob-jd-grid">
              {drafts.map((draft) => (
                <JdCard draft={draft} onSelectDraft={onSelectDraft} onRequestDelete={onRequestDelete} key={draft.id} />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default function JdLobDashboard({ lob, config, drafts, onSelectDraft, onNewDraft, onDownloadTemplate, onDownloadSampleTemplate, onUploadDraft, onBack, onDeleteDraft }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadNotice, setUploadNotice] = useState(null);

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await onDeleteDraft(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFileSelected = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setIsUploading(true);
    setUploadNotice(null);
    try {
      const warnings = await onUploadDraft(lob, file);
      if (warnings?.length) {
        setUploadNotice({ tone: 'warning', text: warnings.join(' ') });
      }
    } catch (error) {
      setUploadNotice({ tone: 'error', text: error.message || 'Failed to upload JD template.' });
    } finally {
      setIsUploading(false);
    }
  };

  const label = config?.lob_labels?.[lob] || lob;
  const description = config?.lob_descriptions?.[lob];
  const lobDrafts = drafts.filter((d) => d.lob === lob);

  const query = searchQuery.trim().toLowerCase();
  const matchesSearch = (draft) =>
    !query || `${draft.title || ''} ${draft.prepared_by_name || ''}`.toLowerCase().includes(query);

  const draftJds = lobDrafts.filter((d) => d.status === 'draft' && matchesSearch(d));
  const completedJds = lobDrafts.filter((d) => d.status === 'generated' && matchesSearch(d));

  const showDrafts = statusFilter === 'all' || statusFilter === 'draft';
  const showCompleted = statusFilter === 'all' || statusFilter === 'generated';
  const accentClass = lob === 'NBFC' ? 'accent-nbfc' : 'accent-amc';

  const draftEmptyText = query
    ? 'No drafts match your search.'
    : 'No JDs in progress for this line of business yet — start one above.';
  const completedEmptyText = query ? 'No completed JDs match your search.' : 'No completed JDs yet.';

  return (
    <div className={`jd-lob-dashboard ${accentClass}`}>
      <button className="jd-lob-back" onClick={onBack}>
        ← Change Line of Business
      </button>

      <div className="jd-lob-hero">
        <div className="jd-lob-hero-copy">
          <h2>{label}</h2>
          {description && <p className="jd-lob-hero-subtitle">{description} - {lob} Job Descriptions</p>}
        </div>

        <div className="jd-lob-hero-actions">
          <label className="jd-lob-search">
            <SearchIcon />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title or preparer"
              aria-label="Search job descriptions"
            />
          </label>

          <select
            className="jd-lob-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by status"
          >
            <option value="all">All statuses</option>
            <option value="draft">Drafts only</option>
            <option value="generated">Completed only</option>
          </select>

          <button className="jd-lob-template-btn" onClick={() => onDownloadTemplate(lob)}>
            <DownloadIcon />
            Download Template
          </button>

          <button className="jd-lob-template-btn" onClick={() => onDownloadSampleTemplate(lob)}>
            <DownloadIcon />
            Download Sample (Filled)
          </button>

          <label className="jd-lob-template-btn jd-lob-upload-btn">
            <UploadIcon />
            {isUploading ? 'Uploading…' : 'Upload Filled Template'}
            <input
              type="file"
              accept=".xlsx"
              onChange={handleFileSelected}
              disabled={isUploading}
              hidden
            />
          </label>

          <button className="jd-lob-new-btn" onClick={() => onNewDraft(lob)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New Job Description
          </button>
        </div>
      </div>

      {uploadNotice && (
        <div className={`jd-lob-upload-notice tone-${uploadNotice.tone}`}>
          {uploadNotice.text}
          <button className="jd-lob-upload-notice-close" onClick={() => setUploadNotice(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      {showDrafts && (
        <JdStatusSection
          title="Drafts"
          tone="draft"
          count={draftJds.length}
          emptyText={draftEmptyText}
          drafts={draftJds}
          onSelectDraft={onSelectDraft}
          onRequestDelete={setDeleteTarget}
        />
      )}

      {showCompleted && (
        <JdStatusSection
          title="Completed"
          tone="completed"
          count={completedJds.length}
          emptyText={completedEmptyText}
          drafts={completedJds}
          onSelectDraft={onSelectDraft}
          onRequestDelete={setDeleteTarget}
        />
      )}

      <JdConfirmDialog
        open={!!deleteTarget}
        title="Delete this JD?"
        message={`"${deleteTarget?.title}" will be permanently deleted. This can't be undone.`}
        confirmLabel="Delete JD"
        isBusy={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
