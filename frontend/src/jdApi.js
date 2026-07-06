/**
 * API client for the JD Creator backend.
 */

const API_BASE =
  window.location.hostname === 'localhost'
    ? 'http://localhost:8001'
    : 'https://llm-council-containerapp.nicedesert-691670aa.southindia.azurecontainerapps.io';

export const jdApi = {
  /** Get dropdown options / thresholds / step order. */
  async getConfig() {
    const response = await fetch(`${API_BASE}/api/jd/config`);
    if (!response.ok) {
      throw new Error('Failed to load JD config');
    }
    return response.json();
  },

  /** List all JD drafts (metadata only). */
  async listDrafts() {
    const response = await fetch(`${API_BASE}/api/jd/drafts`);
    if (!response.ok) {
      throw new Error('Failed to list JD drafts');
    }
    return response.json();
  },

  /** Create a new JD draft for a line of business. */
  async createDraft(lob) {
    const response = await fetch(`${API_BASE}/api/jd/drafts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lob }),
    });
    if (!response.ok) {
      throw new Error('Failed to create JD draft');
    }
    return response.json();
  },

  /** Get a specific JD draft. */
  async getDraft(id) {
    const response = await fetch(`${API_BASE}/api/jd/drafts/${id}`);
    if (!response.ok) {
      throw new Error('Failed to load JD draft');
    }
    return response.json();
  },

  /** Save a single wizard step's data. */
  async saveStep(id, stepKey, stepData) {
    const response = await fetch(
      `${API_BASE}/api/jd/drafts/${id}/steps/${stepKey}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stepData),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to save JD step');
    }
    return response.json();
  },

  /** Reset a single wizard step back to its blank default. */
  async clearStep(id, stepKey) {
    const response = await fetch(
      `${API_BASE}/api/jd/drafts/${id}/steps/${stepKey}/clear`,
      { method: 'POST' }
    );
    if (!response.ok) {
      throw new Error('Failed to clear JD step');
    }
    return response.json();
  },

  /** Permanently delete a JD draft. */
  async deleteDraft(id) {
    const response = await fetch(`${API_BASE}/api/jd/drafts/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete JD draft');
    }
    return response.json();
  },

  /** Validate + flip a draft's status to "generated". */
  async generate(id) {
    const response = await fetch(`${API_BASE}/api/jd/drafts/${id}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const error = new Error('Failed to generate JD');
      error.details = errorBody.detail;
      throw error;
    }
    return response.json();
  },

  /** Lazily create/fetch the council conversation linked to this JD. */
  async linkConversation(id) {
    const response = await fetch(
      `${API_BASE}/api/jd/drafts/${id}/link-conversation`,
      { method: 'POST' }
    );
    if (!response.ok) {
      throw new Error('Failed to link conversation');
    }
    return response.json();
  },
};
