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
    <div style={{ marginBottom: 24 }}>
      <h4>{title} (min {min})</h4>
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

export default function JdStepReports({ value, onChange, config, errors }) {
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

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 6: Direct Reports & Relationships</h3>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>

      <h4>A. Job Purpose of Direct Reports</h4>
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
      <button className="jd-add-row-btn" onClick={addDirectReport} style={{ marginBottom: 24 }}>
        + Add Direct Report
      </button>

      <RelationshipTable
        title="B. Internal Relationships"
        rows={data.internal_relationships || []}
        onChange={(rows) => onChange({ ...data, internal_relationships: rows })}
        frequencyOptions={frequencyOptions}
        min={minInternal}
        errorMsg={errors?.internal_relationships}
      />

      <RelationshipTable
        title="C. External Relationships"
        rows={data.external_relationships || []}
        onChange={(rows) => onChange({ ...data, external_relationships: rows })}
        frequencyOptions={frequencyOptions}
        min={minExternal}
        errorMsg={errors?.external_relationships}
      />
    </div>
  );
}
