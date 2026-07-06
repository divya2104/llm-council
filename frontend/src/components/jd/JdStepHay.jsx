import { useState } from 'react';

function TagInput({ tags, onChange, placeholder }) {
  const [input, setInput] = useState('');

  const addTag = () => {
    const trimmed = input.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInput('');
  };

  const removeTag = (tag) => onChange(tags.filter((t) => t !== tag));

  return (
    <div>
      <input
        type="text"
        value={input}
        placeholder={placeholder}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            addTag();
          }
        }}
      />
      <div className="jd-tag-list">
        {tags.map((tag) => (
          <div className="jd-tag-chip" key={tag}>
            {tag}
            <button onClick={() => removeTag(tag)}>×</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function JdStepHay({ value, onChange, config, errors }) {
  const hay = value || { know_how: {}, decision_making: {}, problem_solving: {} };
  const knowHow = hay.know_how || {};
  const decisionMaking = hay.decision_making || {};
  const problemSolving = hay.problem_solving || {};

  const setKnowHow = (field, val) => onChange({ ...hay, know_how: { ...knowHow, [field]: val } });
  const setDecisionMaking = (field, val) => onChange({ ...hay, decision_making: { ...decisionMaking, [field]: val } });
  const setProblemSolving = (field, val) => onChange({ ...hay, problem_solving: { ...problemSolving, [field]: val } });

  const qualificationOptions = config?.minimum_qualification_options || [];
  const industryOptions = config?.industry_experience_options || [];
  const ambiguityLevels = config?.ambiguity_levels || [];

  const toggleQualification = (qual) => {
    const current = knowHow.min_qualification || [];
    if (current.includes(qual)) {
      setKnowHow('min_qualification', current.filter((q) => q !== qual));
    } else {
      setKnowHow('min_qualification', [...current, qual]);
    }
  };

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 7: Hay Factors</h3>
      </div>

      <div className="jd-step-title">
        <h4 style={{ margin: 0 }}>1. Know-How Requirements</h4>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>
      <div className="jd-field-grid">
        <div className={`jd-field ${errors?.min_qualification ? 'has-error' : ''}`}>
          <label>Minimum Qualification *</label>
          <div className="jd-checkbox-group">
            {qualificationOptions.map((q) => (
              <label key={q}>
                <input
                  type="checkbox"
                  checked={(knowHow.min_qualification || []).includes(q)}
                  onChange={() => toggleQualification(q)}
                />
                {q}
              </label>
            ))}
          </div>
          {errors?.min_qualification && <div className="jd-field-error">{errors.min_qualification}</div>}
        </div>

        <div className={`jd-field ${errors?.years_of_experience ? 'has-error' : ''}`}>
          <label>Years of Experience *</label>
          <input
            type="text"
            placeholder="e.g. 15-20 years"
            value={knowHow.years_of_experience || ''}
            onChange={(e) => setKnowHow('years_of_experience', e.target.value)}
          />
          {errors?.years_of_experience && <div className="jd-field-error">{errors.years_of_experience}</div>}
        </div>
      </div>

      <div className={`jd-field ${errors?.technical_expertise_areas ? 'has-error' : ''}`}>
        <label>Technical Expertise Areas * (press Enter to add)</label>
        <TagInput
          tags={knowHow.technical_expertise_areas || []}
          onChange={(tags) => setKnowHow('technical_expertise_areas', tags)}
          placeholder="e.g. Fund Accounting"
        />
        {errors?.technical_expertise_areas && <div className="jd-field-error">{errors.technical_expertise_areas}</div>}
      </div>

      <div className="jd-field-grid">
        <div className="jd-field">
          <label>Certifications (optional)</label>
          <input
            type="text"
            placeholder="e.g. CFA Level 3, FRM"
            value={knowHow.certifications || ''}
            onChange={(e) => setKnowHow('certifications', e.target.value)}
          />
        </div>

        <div className={`jd-field ${errors?.industry_experience ? 'has-error' : ''}`}>
          <label>Industry Experience *</label>
          <select
            value={knowHow.industry_experience || ''}
            onChange={(e) => setKnowHow('industry_experience', e.target.value)}
          >
            <option value="">Select</option>
            {industryOptions.map((i) => <option value={i} key={i}>{i}</option>)}
          </select>
          {errors?.industry_experience && <div className="jd-field-error">{errors.industry_experience}</div>}
        </div>
      </div>

      <div className="jd-step-title">
        <h4 style={{ margin: 0 }}>2. Decision-Making Authority</h4>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>
      <div className="jd-field-grid">
        <div className={`jd-field ${errors?.independent_decisions ? 'has-error' : ''}`}>
          <label>Independent Decisions *</label>
          <textarea
            rows={3}
            placeholder="e.g. Approve expense budgets up to ₹5 Cr, hire within approved headcount..."
            value={decisionMaking.independent_decisions || ''}
            onChange={(e) => setDecisionMaking('independent_decisions', e.target.value)}
          />
          {errors?.independent_decisions && <div className="jd-field-error">{errors.independent_decisions}</div>}
        </div>
        <div className={`jd-field ${errors?.decisions_needing_approval ? 'has-error' : ''}`}>
          <label>Decisions Needing Approval *</label>
          <textarea
            rows={3}
            placeholder="e.g. Capital expenditure > ₹5 Cr requires CEO approval..."
            value={decisionMaking.decisions_needing_approval || ''}
            onChange={(e) => setDecisionMaking('decisions_needing_approval', e.target.value)}
          />
          {errors?.decisions_needing_approval && <div className="jd-field-error">{errors.decisions_needing_approval}</div>}
        </div>
        <div className={`jd-field ${errors?.financial_approval_limit ? 'has-error' : ''}`}>
          <label>Financial Approval Limit *</label>
          <input
            type="text"
            placeholder="₹ ___ Cr (independently)"
            value={decisionMaking.financial_approval_limit || ''}
            onChange={(e) => setDecisionMaking('financial_approval_limit', e.target.value)}
          />
          {errors?.financial_approval_limit && <div className="jd-field-error">{errors.financial_approval_limit}</div>}
        </div>
        <div className={`jd-field ${errors?.advisory_vs_final_authority ? 'has-error' : ''}`}>
          <label>Advisory vs Final Authority *</label>
          <input
            type="text"
            placeholder="e.g. Advisory on pricing, Final on compliance"
            value={decisionMaking.advisory_vs_final_authority || ''}
            onChange={(e) => setDecisionMaking('advisory_vs_final_authority', e.target.value)}
          />
          {errors?.advisory_vs_final_authority && <div className="jd-field-error">{errors.advisory_vs_final_authority}</div>}
        </div>
      </div>

      <div className="jd-step-title">
        <h4 style={{ margin: 0 }}>3. Problem Solving Context</h4>
        <span className="jd-badge recommended">Recommended</span>
      </div>
      <p className="jd-step-help">Optional — does not block JD generation, but improves scoring accuracy.</p>
      <div className="jd-field-grid">
        <div className="jd-field">
          <label>Thinking Environment</label>
          <textarea
            rows={2}
            placeholder="Describe how structured or ambiguous the role's operating environment is..."
            value={problemSolving.thinking_environment || ''}
            onChange={(e) => setProblemSolving('thinking_environment', e.target.value)}
          />
        </div>
        <div className="jd-field">
          <label>Types of Problems Encountered</label>
          <textarea
            rows={2}
            placeholder="List typical problems this role solves..."
            value={problemSolving.types_of_problems || ''}
            onChange={(e) => setProblemSolving('types_of_problems', e.target.value)}
          />
        </div>
        <div className="jd-field">
          <label>Degree of Ambiguity</label>
          <select
            value={problemSolving.degree_of_ambiguity || ''}
            onChange={(e) => setProblemSolving('degree_of_ambiguity', e.target.value)}
          >
            <option value="">Select</option>
            {ambiguityLevels.map((a) => <option value={a} key={a}>{a}</option>)}
          </select>
        </div>
      </div>
    </div>
  );
}
