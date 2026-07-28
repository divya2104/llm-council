export default function JdStepDimensions({ value, onChange }) {
  const dimensions = value || { rows: [] };
  const rows = dimensions.rows || [];

  const updateRow = (id, field, val) => {
    onChange({ rows: rows.map((r) => (r.id === id ? { ...r, [field]: val } : r)) });
  };

  const addRow = () => {
    const nextId = Math.max(0, ...rows.map((r) => r.id)) + 1;
    onChange({ rows: [...rows, { id: nextId, dimension_name: '', fy_previous: '', fy_current: '', remarks: '' }] });
  };

  const removeRow = (id) => {
    onChange({ rows: rows.filter((r) => r.id !== id) });
  };

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 3: Dimensions</h3>
        <span className="jd-badge negotiable">Negotiable</span>
      </div>
      <p className="jd-step-help">
        Provides quantitative evidence for Accountability scoring (Magnitude sub-factor).
        This section is intentionally blank — each business unit defines its own dimensions
        (e.g. "Total AAUM", "Loan disbursed").
      </p>

      <table className="jd-table">
        <thead>
          <tr>
            <th style={{ width: 40 }}>S.No</th>
            <th>Dimension Name</th>
            <th>FY Previous</th>
            <th>FY Current</th>
            <th>Remarks</th>
            <th style={{ width: 30 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={row.id}>
              <td>{idx + 1}</td>
              <td>
                <input
                  value={row.dimension_name}
                  onChange={(e) => updateRow(row.id, 'dimension_name', e.target.value)}
                  placeholder='e.g. "Total AAUM"'
                />
              </td>
              <td>
                <input
                  value={row.fy_previous}
                  onChange={(e) => updateRow(row.id, 'fy_previous', e.target.value)}
                />
              </td>
              <td>
                <input
                  value={row.fy_current}
                  onChange={(e) => updateRow(row.id, 'fy_current', e.target.value)}
                />
              </td>
              <td>
                <input
                  value={row.remarks}
                  onChange={(e) => updateRow(row.id, 'remarks', e.target.value)}
                />
              </td>
              <td>
                <button className="jd-table-remove" onClick={() => removeRow(row.id)}>×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <button className="jd-add-row-btn" onClick={addRow}>+ Add Row</button>
    </div>
  );
}
