function HierarchyBoxList({ label, boxes, onChange }) {
  const update = (idx, field, val) => {
    const next = boxes.map((b, i) => (i === idx ? { ...b, [field]: val } : b));
    onChange(next);
  };
  const addBox = () => onChange([...boxes, { title: '', band: '' }]);
  const removeBox = (idx) => onChange(boxes.filter((_, i) => i !== idx));

  return (
    <div className="jd-hierarchy-row">
      {boxes.map((box, idx) => (
        <div className="jd-hierarchy-box" key={idx}>
          <strong className="jd-hierarchy-box-label">{label}</strong>
          <input
            placeholder="Role title"
            value={box.title}
            onChange={(e) => update(idx, 'title', e.target.value)}
          />
          <input
            placeholder="Band (e.g. JB 3)"
            value={box.band}
            onChange={(e) => update(idx, 'band', e.target.value)}
          />
          {boxes.length > 1 && (
            <button className="jd-table-remove" onClick={() => removeBox(idx)}>×</button>
          )}
        </div>
      ))}
      <button className="jd-add-row-btn" onClick={addBox} style={{ alignSelf: 'center' }}>
        + Add
      </button>
    </div>
  );
}

export default function JdStepBasics({ value, onChange, config, errors, lob }) {
  const basics = value || {};
  const set = (field, val) => onChange({ ...basics, [field]: val });

  const businessOptions = config?.lob_business_options?.[lob] || [];
  const cityOptions = config?.lob_city_options || [];
  const hierarchyLevels = config?.hierarchy_levels || [];
  const departmentsByFunction = config?.departments_by_function || {};
  const departmentOptions = departmentsByFunction[basics.function] || [];
  const reportsToDepartmentOptions = departmentsByFunction[basics.reports_to_function] || [];

  const visual = basics.org_hierarchy_visual || {};
  const setVisual = (field, val) => set('org_hierarchy_visual', { ...visual, [field]: val });

  const field = (key, label, extra = null) => (
    <div className={`jd-field ${errors?.[key] ? 'has-error' : ''}`}>
      <label>{label} *</label>
      {extra || (
        <input
          type="text"
          value={basics[key] || ''}
          onChange={(e) => set(key, e.target.value)}
        />
      )}
      {errors?.[key] && <div className="jd-field-error">{errors[key]}</div>}
    </div>
  );

  return (
    <div>
      <div className="jd-step-title">
        <h3>Step 1: Basic Details</h3>
        <span className="jd-badge non-negotiable">Non-Negotiable</span>
      </div>
      <p className="jd-step-help">
        These fields establish who the role is, where it sits in the organization, and who it reports to.
      </p>

      <div className="jd-field-group">
        <div className="jd-field-group-heading">Role Identity &amp; Position IDs</div>
        <div className="jd-field-grid">
          <div className="jd-field">
            <label>LOB Selection (locked)</label>
            <input type="text" value={lob} disabled />
          </div>

          {field('poornata_position_number', 'Poornata Position Number')}
          {field('poornata_position_title', 'Poornata Position Title')}
          {field('designation_employee', 'Designation of Employee')}

          {field('org_hierarchy_level', 'Organization Hierarchy Level', (
            <select value={basics.org_hierarchy_level || ''} onChange={(e) => set('org_hierarchy_level', e.target.value)}>
              <option value="">Select band</option>
              {hierarchyLevels.map((l) => <option value={l} key={l}>{l}</option>)}
            </select>
          ))}

          {field('date_of_writing', 'Date of Writing', (
            <input
              type="date"
              value={basics.date_of_writing || ''}
              onChange={(e) => set('date_of_writing', e.target.value)}
            />
          ))}
        </div>
      </div>

      <div className="jd-field-group">
        <div className="jd-field-group-heading">Location &amp; Org Placement</div>
        <div className="jd-field-grid">
          {field('business', 'Business', (
            <input
              list="jd-business-options"
              value={basics.business || ''}
              onChange={(e) => set('business', e.target.value)}
            />
          ))}
          <datalist id="jd-business-options">
            {businessOptions.map((b) => <option value={b} key={b} />)}
          </datalist>

          {field('unit', 'Unit', (
            <input
              type="text"
              maxLength={100}
              value={basics.unit || ''}
              onChange={(e) => set('unit', e.target.value)}
            />
          ))}

          {field('location', 'Location', (
            <input
              list="jd-city-options"
              value={basics.location || ''}
              onChange={(e) => set('location', e.target.value)}
            />
          ))}
          <datalist id="jd-city-options">
            {cityOptions.map((c) => <option value={c} key={c} />)}
          </datalist>

          {field('function', 'Function')}

          {field('department', 'Department', (
            <select value={basics.department || ''} onChange={(e) => set('department', e.target.value)}>
              <option value="">Select department</option>
              {departmentOptions.map((d) => <option value={d} key={d}>{d}</option>)}
            </select>
          ))}
        </div>
      </div>

      <div className="jd-field-group">
        <div className="jd-field-group-heading">Reporting Line</div>
        <div className="jd-field-grid">
          {field('reports_to_position_number', 'Reports To: Position Number')}
          {field('reports_to_position_title', 'Reports To: Position Title')}
          {field('reports_to_function', 'Reports To: Function')}

          {field('reports_to_department', 'Reports To: Department', (
            <select value={basics.reports_to_department || ''} onChange={(e) => set('reports_to_department', e.target.value)}>
              <option value="">Select department</option>
              {reportsToDepartmentOptions.map((d) => <option value={d} key={d}>{d}</option>)}
            </select>
          ))}

          {field('designation_manager', 'Designation of Manager')}
        </div>
      </div>

      <h4>Organization Hierarchy Visual</h4>
      <p className="jd-step-help">
        Build a simple hierarchy showing 2 levels up, 2 levels down, and parallel roles.
      </p>
      <div className="jd-hierarchy-tree">
        <HierarchyBoxList
          label="2 Levels Up"
          boxes={visual.levels_up_2 || []}
          onChange={(v) => setVisual('levels_up_2', v)}
        />
        <HierarchyBoxList
          label="1 Level Up"
          boxes={visual.levels_up_1 || []}
          onChange={(v) => setVisual('levels_up_1', v)}
        />
        <div className="jd-hierarchy-row">
          <div className="jd-hierarchy-box this-role">
            <strong className="jd-hierarchy-box-label this-role">This Role</strong>
            <input
              placeholder="Role title"
              value={visual.this_role?.title || ''}
              onChange={(e) => setVisual('this_role', { ...visual.this_role, title: e.target.value })}
            />
            <input
              placeholder="Band"
              value={visual.this_role?.band || ''}
              onChange={(e) => setVisual('this_role', { ...visual.this_role, band: e.target.value })}
            />
          </div>
          <HierarchyBoxList
            label="Parallel"
            boxes={visual.peers || []}
            onChange={(v) => setVisual('peers', v)}
          />
        </div>
        <HierarchyBoxList
          label="1 Level Down"
          boxes={visual.levels_down_1 || []}
          onChange={(v) => setVisual('levels_down_1', v)}
        />
        <HierarchyBoxList
          label="2 Levels Down"
          boxes={visual.levels_down_2 || []}
          onChange={(v) => setVisual('levels_down_2', v)}
        />
      </div>
    </div>
  );
}
