export default function JdStepPurpose({ value, onChange, config, errors }) {
  const purpose = value || {};
  const min = config?.job_purpose_min_chars ?? 100;
  const max = config?.job_purpose_max_chars ?? 2000;
  const len = (purpose.text || '').length;

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 2: Job Purpose</h3>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>
      <p className="jd-step-help">
        Guided Prompt: Describe the overall purpose of this role in 3-5 sentences. Include:
        (1) What is the primary mission? (2) What functions/areas does it oversee?
        (3) What is its strategic importance? (4) Who does it advise or support?
      </p>

      <div className={`jd-field ${errors?.text ? 'has-error' : ''}`}>
        <textarea
          rows={8}
          value={purpose.text || ''}
          onChange={(e) => onChange({ ...purpose, text: e.target.value })}
        />
        <div className="jd-char-counter">
          {len} / {max} (min {min})
        </div>
        {errors?.text && <div className="jd-field-error">{errors.text}</div>}
      </div>
      <div className="jd-note">AI will enhance language to Hay style (coming in Phase 2).</div>
    </div>
  );
}
