/**
 * Plain-JS validators for the JD Creator wizard.
 *
 * These mirror `_validate_for_generate` in backend/jd.py — keep the two in
 * sync manually since there's no shared-language validation library.
 */

const REQUIRED_BASICS_FIELDS = [
  'business', 'unit', 'location', 'poornata_position_number',
  'reports_to_position_number', 'poornata_position_title',
  'reports_to_position_title', 'function', 'reports_to_function',
  'department', 'reports_to_department', 'designation_employee',
  'designation_manager', 'org_hierarchy_level', 'date_of_writing',
];

const FIELD_LABELS = {
  business: 'Business',
  unit: 'Unit',
  location: 'Location',
  poornata_position_number: 'Poornata Position Number',
  reports_to_position_number: 'Reports To: Position Number',
  poornata_position_title: 'Poornata Position Title',
  reports_to_position_title: 'Reports To: Position Title',
  function: 'Function',
  reports_to_function: 'Reports To: Function',
  department: 'Department',
  reports_to_department: 'Reports To: Department',
  designation_employee: 'Designation of Employee',
  designation_manager: 'Designation of Manager',
  org_hierarchy_level: 'Organization Hierarchy Level',
  date_of_writing: 'Date of Writing',
};

export function validateBasics(basics = {}) {
  const errors = {};
  REQUIRED_BASICS_FIELDS.forEach((f) => {
    if (!String(basics[f] || '').trim()) {
      errors[f] = `${FIELD_LABELS[f] || f} is required`;
    }
  });
  return { valid: Object.keys(errors).length === 0, errors };
}

export function validatePurpose(purpose = {}, config = {}) {
  const min = config.job_purpose_min_chars ?? 100;
  const max = config.job_purpose_max_chars ?? 2000;
  const len = (purpose.text || '').length;
  const errors = {};
  if (len < min || len > max) {
    errors.text = `Must be between ${min} and ${max} characters (currently ${len})`;
  }
  return { valid: Object.keys(errors).length === 0, errors };
}

export function validateDimensions() {
  // NEGOTIABLE — always valid, kept for symmetry with other step validators.
  return { valid: true, errors: {} };
}

export function validateContext(context = {}, config = {}) {
  const minContextChars = config.job_context_min_chars ?? 200;
  const minChallenges = config.min_challenges ?? 3;
  const errors = {};
  if ((context.job_context || '').length < minContextChars) {
    errors.job_context = `Must be at least ${minContextChars} characters`;
  }
  const challenges = (context.key_challenges || []).filter((c) => String(c || '').trim());
  if (challenges.length < minChallenges) {
    errors.key_challenges = `At least ${minChallenges} distinct challenges required`;
  }
  return { valid: Object.keys(errors).length === 0, errors };
}

export function validateAccountabilities(accountabilities = {}, config = {}) {
  const min = config.min_accountabilities ?? 5;
  const rows = (accountabilities.rows || []).filter(
    (r) => String(r.accountability || '').trim() && String(r.supporting_actions || '').trim()
  );
  const errors = {};
  if (rows.length < min) {
    errors.rows = `At least ${min} accountabilities required (currently ${rows.length})`;
  }
  return { valid: Object.keys(errors).length === 0, errors };
}

export function validateReports(reportsAndRelationships = {}, config = {}) {
  const minInternal = config.min_internal_relationships ?? 3;
  const minExternal = config.min_external_relationships ?? 2;
  const errors = {};
  const internal = (reportsAndRelationships.internal_relationships || []).filter(
    (r) => String(r.stakeholder || '').trim()
  );
  if (internal.length < minInternal) {
    errors.internal_relationships = `At least ${minInternal} internal relationships required`;
  }
  const external = (reportsAndRelationships.external_relationships || []).filter(
    (r) => String(r.stakeholder || '').trim()
  );
  if (external.length < minExternal) {
    errors.external_relationships = `At least ${minExternal} external relationships required`;
  }
  return { valid: Object.keys(errors).length === 0, errors };
}

export function validateHay(hayFactors = {}) {
  const errors = {};
  const knowHow = hayFactors.know_how || {};
  const decisionMaking = hayFactors.decision_making || {};

  if (!(knowHow.min_qualification || []).length) {
    errors.min_qualification = 'Minimum qualification is required';
  }
  if (!String(knowHow.years_of_experience || '').trim()) {
    errors.years_of_experience = 'Years of experience is required';
  }
  if (!(knowHow.technical_expertise_areas || []).length) {
    errors.technical_expertise_areas = 'At least one technical expertise area is required';
  }
  if (!String(knowHow.industry_experience || '').trim()) {
    errors.industry_experience = 'Industry experience is required';
  }

  ['independent_decisions', 'decisions_needing_approval', 'financial_approval_limit', 'advisory_vs_final_authority'].forEach((f) => {
    if (!String(decisionMaking[f] || '').trim()) {
      errors[f] = 'This field is required';
    }
  });

  // problem_solving is RECOMMENDED/optional — never validated here.
  return { valid: Object.keys(errors).length === 0, errors };
}

export function validateSignOff(signOff = {}) {
  const errors = {};
  if (!String(signOff.prepared_by_name || '').trim()) {
    errors.prepared_by_name = 'Name is required';
  }
  if (!String(signOff.prepared_by_email || '').trim()) {
    errors.prepared_by_email = 'Email is required';
  }
  if (!signOff.confirmed) {
    errors.confirmed = 'Confirmation checkbox must be checked';
  }
  return { valid: Object.keys(errors).length === 0, errors };
}

const STEP_VALIDATORS = {
  basics: (draft, config) => validateBasics(draft.basics, config),
  purpose: (draft, config) => validatePurpose(draft.purpose, config),
  dimensions: (draft, config) => validateDimensions(draft.dimensions, config),
  context: (draft, config) => validateContext(draft.context, config),
  accountabilities: (draft, config) => validateAccountabilities(draft.accountabilities, config),
  reports_and_relationships: (draft, config) => validateReports(draft.reports_and_relationships, config),
  hay_factors: (draft, config) => validateHay(draft.hay_factors, config),
  sign_off: (draft, config) => validateSignOff(draft.sign_off, config),
};

const NON_NEGOTIABLE_STEPS = [
  'basics', 'purpose', 'context', 'accountabilities',
  'reports_and_relationships', 'hay_factors', 'sign_off',
];

export function validateFullDraftForGenerate(draft, config = {}) {
  const stepErrors = {};
  NON_NEGOTIABLE_STEPS.forEach((stepKey) => {
    const result = STEP_VALIDATORS[stepKey](draft, config);
    if (!result.valid) {
      stepErrors[stepKey] = result.errors;
    }
  });
  return { valid: Object.keys(stepErrors).length === 0, stepErrors };
}

/** Per-step completion (including the negotiable "dimensions" step, which is always complete)
 * for driving the stepper's green/yellow state — independent of navigation history. */
export function getStepCompletionMap(draft, config = {}) {
  const map = {};
  Object.keys(STEP_VALIDATORS).forEach((stepKey) => {
    map[stepKey] = STEP_VALIDATORS[stepKey](draft, config).valid;
  });
  return map;
}
