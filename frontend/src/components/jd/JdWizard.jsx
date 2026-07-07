import { useState, useEffect, useRef } from 'react';
import { jdApi } from '../../jdApi';
import { validateFullDraftForGenerate, getStepCompletionMap } from './JdValidation';
import JdConfirmDialog from './JdConfirmDialog';
import JdStepBasics from './JdStepBasics';
import JdStepPurpose from './JdStepPurpose';
import JdStepDimensions from './JdStepDimensions';
import JdStepContext from './JdStepContext';
import JdStepAccountabilities from './JdStepAccountabilities';
import JdStepReports from './JdStepReports';
import JdStepHay from './JdStepHay';
import JdStepSignOff from './JdStepSignOff';
import './JdWizard.css';

const STEP_COMPONENTS = {
  basics: JdStepBasics,
  purpose: JdStepPurpose,
  dimensions: JdStepDimensions,
  context: JdStepContext,
  accountabilities: JdStepAccountabilities,
  reports_and_relationships: JdStepReports,
  hay_factors: JdStepHay,
  sign_off: JdStepSignOff,
};

const AUTOSAVE_DELAY_MS = 800;

const STEP_CAPTIONS = {
  basics: 'Role identity & reporting line',
  purpose: 'Why this role exists',
  dimensions: 'Scope, in numbers',
  context: 'Environment & challenges',
  accountabilities: 'Key accountabilities',
  reports_and_relationships: 'Stakeholders & relationships',
  hay_factors: 'Hay evaluation factors',
  sign_off: 'Review & submit',
};

function IncompleteStepIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 6h12M8 12h12M8 18h12" />
      <path d="M3 6h.01M3 12h.01M3 18h.01" />
    </svg>
  );
}

export default function JdWizard({ draft, config, onDraftUpdated, onBackToDashboard, onDeleteDraft }) {
  const [localDraft, setLocalDraft] = useState(draft);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [hasAttemptedSubmit, setHasAttemptedSubmit] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  const saveTimerRef = useRef(null);
  const pendingStepRef = useRef(null);
  const localDraftRef = useRef(localDraft);

  useEffect(() => {
    localDraftRef.current = localDraft;
  }, [localDraft]);

  useEffect(() => {
    setLocalDraft(draft);
  }, [draft]);

  useEffect(() => {
    setCurrentStepIndex(0);
  }, [draft.id]);

  const steps = config?.wizard_steps || [
    { key: 'basics', label: 'Basics' },
    { key: 'purpose', label: 'Purpose' },
    { key: 'dimensions', label: 'Dims' },
    { key: 'context', label: 'Context' },
    { key: 'accountabilities', label: 'Accts' },
    { key: 'reports_and_relationships', label: 'Reports' },
    { key: 'hay_factors', label: 'Hay' },
    { key: 'sign_off', label: 'Sign-Off' },
  ];

  const currentStep = steps[currentStepIndex];
  const StepComponent = STEP_COMPONENTS[currentStep.key];

  const { stepErrors: fullStepErrors } = validateFullDraftForGenerate(localDraft, config || {});
  // Fields only turn red once the user has actually tried to submit at Sign-Off.
  const stepErrors = hasAttemptedSubmit ? fullStepErrors : {};
  const stepCompletionMap = getStepCompletionMap(localDraft, config || {});

  const flushSave = async (stepKey) => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    const keyToSave = stepKey || pendingStepRef.current;
    if (!keyToSave) return;
    pendingStepRef.current = null;
    setSaveStatus('Saving...');
    try {
      const latestDraft = localDraftRef.current;
      await jdApi.saveStep(latestDraft.id, keyToSave, latestDraft[keyToSave]);
      setSaveStatus('Saved');
    } catch (err) {
      console.error('Failed to save step:', err);
      setSaveStatus('Save failed');
    }
  };

  const handleStepChange = (newStepData) => {
    const stepKey = currentStep.key;
    setLocalDraft((prev) => ({ ...prev, [stepKey]: newStepData }));
    pendingStepRef.current = stepKey;

    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      flushSave(stepKey);
    }, AUTOSAVE_DELAY_MS);
  };

  const goToStep = async (index) => {
    await flushSave();
    setCurrentStepIndex(index);
  };

  const handlePrev = () => goToStep(Math.max(0, currentStepIndex - 1));
  const handleNext = () => goToStep(Math.min(steps.length - 1, currentStepIndex + 1));

  const handleGenerate = async () => {
    await flushSave();
    setHasAttemptedSubmit(true);
    const { valid } = validateFullDraftForGenerate(localDraftRef.current, config || {});
    if (!valid) return;

    setIsGenerating(true);
    setGenerateError(null);
    try {
      const updated = await jdApi.generate(localDraft.id);
      setLocalDraft(updated);
      onDraftUpdated(updated);
    } catch (err) {
      console.error('Failed to generate JD:', err);
      setGenerateError(err.details?.errors || { general: ['Failed to generate JD'] });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveDraft = async () => {
    setIsSavingDraft(true);
    try {
      await flushSave(currentStep.key);
    } finally {
      setIsSavingDraft(false);
    }
  };

  const handleClearStep = async () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    pendingStepRef.current = null;

    setIsClearing(true);
    try {
      const updated = await jdApi.clearStep(localDraft.id, currentStep.key);
      setLocalDraft(updated);
      onDraftUpdated(updated);
      setSaveStatus('Cleared');
    } catch (err) {
      console.error('Failed to clear step:', err);
      setSaveStatus('Clear failed');
    } finally {
      setIsClearing(false);
      setConfirmClearOpen(false);
    }
  };

  const handleDeleteDraft = async () => {
    setIsDeleting(true);
    try {
      await onDeleteDraft(localDraft.id);
    } finally {
      setIsDeleting(false);
      setConfirmDeleteOpen(false);
    }
  };

  const stepProps = {
    value: localDraft[currentStep.key],
    onChange: handleStepChange,
    config,
    errors: stepErrors[currentStep.key] || generateError?.[currentStep.key] || {},
    lob: localDraft.lob,
  };

  if (currentStep.key === 'sign_off') {
    stepProps.generateSummary = stepErrors;
    stepProps.onGenerate = handleGenerate;
    stepProps.isGenerating = isGenerating;
  }

  return (
    <div className="jd-wizard">
      <div className="jd-wizard-rail">
        {onBackToDashboard && (
          <button className="jd-wizard-back-btn" onClick={onBackToDashboard}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
            Back to {localDraft.lob} JDs
          </button>
        )}

        <div className="jd-wizard-rail-heading">
          <div className="jd-wizard-rail-lob-group">
            <span className={`jd-wizard-rail-lob ${localDraft.lob === 'NBFC' ? 'accent-nbfc' : 'accent-amc'}`}>
              {localDraft.lob}
            </span>
          </div>

          {onDeleteDraft && (
            <button
              className="jd-danger-btn jd-wizard-delete-btn"
              onClick={() => setConfirmDeleteOpen(true)}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 7h16" />
                <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                <path d="M18 7l-.8 13a1 1 0 0 1-1 1H7.8a1 1 0 0 1-1-1L6 7" />
                <path d="M10 11v6M14 11v6" />
              </svg>
              Delete JD
            </button>
          )}
        </div>

        <div className="jd-stepper">
          {steps.map((step, idx) => {
            const isComplete = !!stepCompletionMap[step.key];
            return (
              <div
                key={step.key}
                className={`jd-stepper-item ${idx === currentStepIndex ? 'active' : ''} ${
                  isComplete ? 'completed' : 'incomplete'
                } ${stepErrors[step.key] ? 'has-error' : ''}`}
                onClick={() => goToStep(idx)}
              >
                <span className="jd-stepper-node">
                  {isComplete ? '✓' : <IncompleteStepIcon />}
                </span>
                <span className="jd-stepper-text">
                  <span className="jd-stepper-label">{step.label}</span>
                  <span className="jd-stepper-caption">{STEP_CAPTIONS[step.key]}</span>
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="jd-wizard-main">
        <div className="jd-wizard-body">
          {localDraft.jd_number && <div className="jd-wizard-body-id">{localDraft.jd_number}</div>}
          <StepComponent {...stepProps} />
        </div>

        <div className="jd-wizard-footer">
          <div className="jd-wizard-footer-left">
            <button className="jd-nav-btn secondary" onClick={handlePrev} disabled={currentStepIndex === 0}>
              ← Back
            </button>
            <button className="jd-danger-btn jd-clear-step-btn" onClick={() => setConfirmClearOpen(true)}>
              Clear content
            </button>
          </div>
          <span className="jd-autosave-status">{saveStatus}</span>
          <div className="jd-wizard-footer-right">
            <button className="jd-nav-btn save-draft" onClick={handleSaveDraft} disabled={isSavingDraft}>
              {isSavingDraft ? 'Saving…' : 'Save Draft'}
            </button>
            {currentStepIndex < steps.length - 1 && (
              <button className="jd-nav-btn primary" onClick={handleNext}>
                Next →
              </button>
            )}
          </div>
        </div>
      </div>

      <JdConfirmDialog
        open={confirmDeleteOpen}
        title="Delete this JD?"
        message={`This job description and everything filled in so far will be permanently deleted. This can't be undone.`}
        confirmLabel="Delete JD"
        isBusy={isDeleting}
        onConfirm={handleDeleteDraft}
        onCancel={() => setConfirmDeleteOpen(false)}
      />

      <JdConfirmDialog
        open={confirmClearOpen}
        title={`Clear content on "${currentStep.label}"?`}
        message="Every field on this step will be reset to blank. Other steps are not affected. This can't be undone."
        confirmLabel="Clear content"
        isBusy={isClearing}
        onConfirm={handleClearStep}
        onCancel={() => setConfirmClearOpen(false)}
      />
    </div>
  );
}
