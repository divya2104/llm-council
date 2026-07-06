import './JdConfirmDialog.css';

export default function JdConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isBusy = false,
  onConfirm,
  onCancel,
}) {
  if (!open) return null;

  return (
    <div className="jd-confirm-overlay" onClick={onCancel}>
      <div className="jd-confirm-dialog" role="alertdialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="jd-confirm-actions">
          <button className="jd-nav-btn secondary" onClick={onCancel} disabled={isBusy}>
            {cancelLabel}
          </button>
          <button className="jd-confirm-danger-btn" onClick={onConfirm} disabled={isBusy}>
            {isBusy ? 'Please wait…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
