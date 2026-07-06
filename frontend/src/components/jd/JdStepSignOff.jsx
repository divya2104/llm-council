export default function JdStepSignOff({ value, onChange, errors, generateSummary, onGenerate, isGenerating }) {
  const signOff = value || {};

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 8: Sign-Off</h3>
      </div>
      <p className="jd-step-help">
        Keeping sign-off simple — no digital signatures. Checking the box below is required
        before generating the JD.
      </p>

      <div className="jd-field-grid">
        <div className={`jd-field ${errors?.prepared_by_name ? 'has-error' : ''}`}>
          <label>Prepared By: Name *</label>
          <input
            type="text"
            value={signOff.prepared_by_name || ''}
            onChange={(e) => onChange({ ...signOff, prepared_by_name: e.target.value })}
          />
          {errors?.prepared_by_name && <div className="jd-field-error">{errors.prepared_by_name}</div>}
        </div>
        <div className={`jd-field ${errors?.prepared_by_email ? 'has-error' : ''}`}>
          <label>Prepared By: Email *</label>
          <input
            type="text"
            value={signOff.prepared_by_email || ''}
            onChange={(e) => onChange({ ...signOff, prepared_by_email: e.target.value })}
          />
          {errors?.prepared_by_email && <div className="jd-field-error">{errors.prepared_by_email}</div>}
        </div>
      </div>

      <div className={`jd-field ${errors?.confirmed ? 'has-error' : ''}`}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            checked={!!signOff.confirmed}
            onChange={(e) => onChange({ ...signOff, confirmed: e.target.checked })}
          />
          I confirm that the information provided in this Job Description is accurate and
          complete to the best of my knowledge.
        </label>
        {errors?.confirmed && <div className="jd-field-error">{errors.confirmed}</div>}
      </div>

      {generateSummary && Object.keys(generateSummary).length > 0 && (
        <div className="jd-generate-summary">
          Some sections are incomplete:
          <ul>
            {Object.entries(generateSummary).map(([stepKey, stepErrs]) => (
              <li key={stepKey}>
                {stepKey}: {Object.values(stepErrs).join('; ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="jd-nav-btn primary"
        onClick={onGenerate}
        disabled={isGenerating || (generateSummary && Object.keys(generateSummary).length > 0)}
      >
        {isGenerating ? 'Generating...' : 'Generate JD'}
      </button>
    </div>
  );
}
