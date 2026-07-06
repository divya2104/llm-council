export default function JdStepAccountabilities({ value, onChange, config, errors }) {
  const accountabilities = value || { rows: [] };
  const rows = accountabilities.rows || [];
  const min = config?.min_accountabilities ?? 5;
  const max = config?.max_accountabilities ?? 15;

  const updateRow = (id, field, val) => {
    onChange({ rows: rows.map((r) => (r.id === id ? { ...r, [field]: val } : r)) });
  };

  const addRow = () => {
    if (rows.length >= max) return;
    const nextId = Math.max(0, ...rows.map((r) => r.id)) + 1;
    onChange({ rows: [...rows, { id: nextId, accountability: '', supporting_actions: '' }] });
  };

  const removeRow = (id) => {
    onChange({ rows: rows.filter((r) => r.id !== id) });
  };

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 5: Principal Accountabilities</h3>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>
      <p className="jd-step-help">
        List {min}-{max} key accountabilities. Common areas: Financial Planning, Business
        Intelligence, Compliance, Product Management, Stakeholder Management, People
        Management, Risk, Operations.
      </p>

      <table className="jd-table">
        <thead>
          <tr>
            <th style={{ width: 30 }}>#</th>
            <th style={{ width: '35%' }}>Accountability</th>
            <th>Supporting Actions</th>
            <th style={{ width: 30 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={row.id}>
              <td>{idx + 1}</td>
              <td>
                <input
                  value={row.accountability}
                  onChange={(e) => updateRow(row.id, 'accountability', e.target.value)}
                  placeholder='e.g. "Financial Planning & Monitoring"'
                />
              </td>
              <td>
                <input
                  value={row.supporting_actions}
                  onChange={(e) => updateRow(row.id, 'supporting_actions', e.target.value)}
                  placeholder="Detailed description of what the role does under this accountability"
                />
              </td>
              <td>
                <button className="jd-table-remove" onClick={() => removeRow(row.id)}>×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="jd-row-count">
        {rows.length} of {max} rows | Min {min} required
      </div>
      {errors?.rows && <div className="jd-field-error">{errors.rows}</div>}

      <button className="jd-add-row-btn" onClick={addRow} disabled={rows.length >= max}>
        + Add Accountability
      </button>
    </div>
  );
}
