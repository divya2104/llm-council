import { useEffect, useRef, useState } from 'react';

const SECTIONS = [
  { key: 'context', label: 'Context' },
  { key: 'key_challenges', label: 'Key Challenges' },
];

export default function JdStepContext({ value, onChange, config, errors, lob }) {
  const [activeSection, setActiveSection] = useState(SECTIONS[0].key);
  const tabRefs = useRef([]);

  const context = value || {};
  const minChars = config?.job_context_min_chars ?? 200;
  const minChallenges = config?.min_challenges ?? 3;
  const maxChallenges = config?.max_challenges ?? 8;
  const challenges = context.key_challenges || [];
  const hasPrefilled = useRef(false);

  useEffect(() => {
    if (
      !hasPrefilled.current &&
      !context.organization_context &&
      config?.lob_org_context_templates?.[lob]
    ) {
      hasPrefilled.current = true;
      onChange({ ...context, organization_context: config.lob_org_context_templates[lob] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config, lob]);

  const updateChallenge = (idx, val) => {
    const next = challenges.map((c, i) => (i === idx ? val : c));
    onChange({ ...context, key_challenges: next });
  };

  const addChallenge = () => {
    if (challenges.length >= maxChallenges) return;
    onChange({ ...context, key_challenges: [...challenges, ''] });
  };

  const removeChallenge = (idx) => {
    onChange({ ...context, key_challenges: challenges.filter((_, i) => i !== idx) });
  };

  const sectionHasError = (key) => (key === 'context' && !!errors?.job_context)
    || (key === 'key_challenges' && !!errors?.key_challenges);

  const handleTabKeyDown = (e, idx) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    e.preventDefault();
    const nextIdx = e.key === 'ArrowRight'
      ? (idx + 1) % SECTIONS.length
      : (idx - 1 + SECTIONS.length) % SECTIONS.length;
    setActiveSection(SECTIONS[nextIdx].key);
    tabRefs.current[nextIdx]?.focus();
  };

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 4: Job Context & Major Challenges</h3>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>

      <div className="jd-subnav-tablist" role="tablist" aria-label="Job context and key challenges">
        {SECTIONS.map((section, idx) => (
          <button
            key={section.key}
            ref={(el) => { tabRefs.current[idx] = el; }}
            role="tab"
            id={`jd-context-tab-${section.key}`}
            aria-selected={activeSection === section.key}
            aria-controls={`jd-context-panel-${section.key}`}
            tabIndex={activeSection === section.key ? 0 : -1}
            className={`jd-subnav-tab ${activeSection === section.key ? 'active' : ''}`}
            onClick={() => setActiveSection(section.key)}
            onKeyDown={(e) => handleTabKeyDown(e, idx)}
          >
            {section.label}
            {sectionHasError(section.key) && <span className="jd-subnav-tab-error-dot" aria-label="Has errors" />}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`jd-context-panel-${activeSection}`}
        aria-labelledby={`jd-context-tab-${activeSection}`}
      >
        {activeSection === 'context' && (
          <>
            <div className="jd-field">
              <label>Organization Context (pre-filled — editable)</label>
              <textarea
                rows={4}
                value={context.organization_context || ''}
                onChange={(e) => onChange({ ...context, organization_context: e.target.value })}
              />
            </div>

            <div className={`jd-field ${errors?.job_context ? 'has-error' : ''}`}>
              <label>Job Context *</label>
              <p className="jd-step-help" style={{ marginBottom: 6 }}>
                Describe the specific context in which this role operates. What functions does it
                lead? What regulatory environment? What key metrics does it track?
              </p>
              <textarea
                rows={5}
                value={context.job_context || ''}
                onChange={(e) => onChange({ ...context, job_context: e.target.value })}
              />
              <div className="jd-char-counter">
                {(context.job_context || '').length} chars (min {minChars})
              </div>
              {errors?.job_context && <div className="jd-field-error">{errors.job_context}</div>}
            </div>
          </>
        )}

        {activeSection === 'key_challenges' && (
          <div className={`jd-field ${errors?.key_challenges ? 'has-error' : ''}`}>
            <label>Key Challenges *</label>
            <p className="jd-step-help" style={{ marginBottom: 6 }}>
              List {minChallenges}-{maxChallenges} major challenges. Consider regulatory changes,
              market dynamics, financial risk, talent, technology, stakeholder complexity.
            </p>
            {challenges.map((c, idx) => (
              <div key={idx} className="jd-challenge-row">
                <input
                  type="text"
                  value={c}
                  onChange={(e) => updateChallenge(idx, e.target.value)}
                  placeholder={`Challenge ${idx + 1}`}
                />
                <button className="jd-table-remove" onClick={() => removeChallenge(idx)}>×</button>
              </div>
            ))}
            {errors?.key_challenges && <div className="jd-field-error">{errors.key_challenges}</div>}
            <button className="jd-add-row-btn" onClick={addChallenge} disabled={challenges.length >= maxChallenges}>
              + Add Challenge
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
