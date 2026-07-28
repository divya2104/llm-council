import { useRef, useState } from 'react';

function RelationshipTable({ title, rows, onChange, frequencyOptions, min, errorMsg }) {
  const updateRow = (id, field, val) => {
    onChange(rows.map((r) => (r.id === id ? { ...r, [field]: val } : r)));
  };
  const addRow = () => {
    const nextId = Math.max(0, ...rows.map((r) => r.id)) + 1;
    onChange([...rows, { id: nextId, stakeholder: '', frequency: '', nature_of_interaction: '' }]);
  };
  const removeRow = (id) => onChange(rows.filter((r) => r.id !== id));

  return (
    <div>
      <div className="jd-field-group-heading">{title} (min {min})</div>
      <table className="jd-table">
        <thead>
          <tr>
            <th>Stakeholder / Role</th>
            <th style={{ width: 140 }}>Frequency</th>
            <th>Nature of Interaction</th>
            <th style={{ width: 30 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <input
                  value={row.stakeholder}
                  onChange={(e) => updateRow(row.id, 'stakeholder', e.target.value)}
                />
              </td>
              <td>
                <select
                  value={row.frequency}
                  onChange={(e) => updateRow(row.id, 'frequency', e.target.value)}
                >
                  <option value="">Select</option>
                  {frequencyOptions.map((f) => <option value={f} key={f}>{f}</option>)}
                </select>
              </td>
              <td>
                <input
                  value={row.nature_of_interaction}
                  onChange={(e) => updateRow(row.id, 'nature_of_interaction', e.target.value)}
                />
              </td>
              <td>
                <button className="jd-table-remove" onClick={() => removeRow(row.id)}>×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {errorMsg && <div className="jd-field-error">{errorMsg}</div>}
      <button className="jd-add-row-btn" onClick={addRow}>+ Add</button>
    </div>
  );
}

const SECTIONS = [
  { key: 'direct_reports', label: 'A. Direct Reports' },
  { key: 'internal_relationships', label: 'B. Internal Relationships' },
  { key: 'external_relationships', label: 'C. External Relationships' },
];

export default function JdStepReports({ value, onChange, config, errors }) {
  const [activeSection, setActiveSection] = useState(SECTIONS[0].key);
  const tabRefs = useRef([]);

  const data = value || { direct_reports: [], internal_relationships: [], external_relationships: [] };
  const frequencyOptions = config?.relationship_frequencies || [];
  const minInternal = config?.min_internal_relationships ?? 3;
  const minExternal = config?.min_external_relationships ?? 2;

  const directReports = data.direct_reports || [];
  const updateDirectReport = (id, field, val) => {
    onChange({ ...data, direct_reports: directReports.map((r) => (r.id === id ? { ...r, [field]: val } : r)) });
  };
  const addDirectReport = () => {
    const nextId = Math.max(0, ...directReports.map((r) => r.id)) + 1;
    onChange({ ...data, direct_reports: [...directReports, { id: nextId, report_title: '', job_purpose: '' }] });
  };
  const removeDirectReport = (id) => {
    onChange({ ...data, direct_reports: directReports.filter((r) => r.id !== id) });
  };

  const sectionHasError = (key) => (key === 'internal_relationships' && !!errors?.internal_relationships)
    || (key === 'external_relationships' && !!errors?.external_relationships);

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
        <h3>Step 6: Direct Reports & Relationships</h3>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>

      <div className="jd-subnav-tablist" role="tablist" aria-label="Direct reports and relationships">
        {SECTIONS.map((section, idx) => (
          <button
            key={section.key}
            ref={(el) => { tabRefs.current[idx] = el; }}
            role="tab"
            id={`jd-reports-tab-${section.key}`}
            aria-selected={activeSection === section.key}
            aria-controls={`jd-reports-panel-${section.key}`}
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
        id={`jd-reports-panel-${activeSection}`}
        aria-labelledby={`jd-reports-tab-${activeSection}`}
      >
        {activeSection === 'direct_reports' && (
          <div>
            <div className="jd-field-group-heading">A. Job Purpose of Direct Reports</div>
            <table className="jd-table">
              <thead>
                <tr>
                  <th>Report Title / Role</th>
                  <th>Job Purpose</th>
                  <th style={{ width: 30 }}></th>
                </tr>
              </thead>
              <tbody>
                {directReports.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <input
                        value={row.report_title}
                        onChange={(e) => updateDirectReport(row.id, 'report_title', e.target.value)}
                      />
                    </td>
                    <td>
                      <input
                        value={row.job_purpose}
                        onChange={(e) => updateDirectReport(row.id, 'job_purpose', e.target.value)}
                      />
                    </td>
                    <td>
                      <button className="jd-table-remove" onClick={() => removeDirectReport(row.id)}>×</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button className="jd-add-row-btn" onClick={addDirectReport}>
              + Add Direct Report
            </button>
          </div>
        )}

        {activeSection === 'internal_relationships' && (
          <RelationshipTable
            title="B. Internal Relationships"
            rows={data.internal_relationships || []}
            onChange={(rows) => onChange({ ...data, internal_relationships: rows })}
            frequencyOptions={frequencyOptions}
            min={minInternal}
            errorMsg={errors?.internal_relationships}
          />
        )}

        {activeSection === 'external_relationships' && (
          <RelationshipTable
            title="C. External Relationships"
            rows={data.external_relationships || []}
            onChange={(rows) => onChange({ ...data, external_relationships: rows })}
            frequencyOptions={frequencyOptions}
            min={minExternal}
            errorMsg={errors?.external_relationships}
          />
        )}
      </div>
    </div>
  );
}
