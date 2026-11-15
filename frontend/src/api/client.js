/**
 * ForenSight Forensic Workbench API Client
 * Configured for development CORS, file streaming, and PDF exports.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

    const headers = {
      'Accept': 'application/json',
      ...options.headers,
    };

    if (!isFormData && !options.isBlob) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      if (options.isBlob) {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.blob();
      }

      const isJson = response.headers.get('content-type')?.includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        const errorMsg = (typeof data === 'object' && data?.detail)
          ? data.detail
          : `HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`[ForenSight API Error] ${options.method || 'GET'} ${url}:`, err);
      throw err;
    }
  }

  /**
   * System Health and Storage Diagnostics
   */
  async getHealth() {
    return this.request('/health');
  }

  /**
   * Phase 3 Real Investigation Dashboard Statistics
   */
  async getDashboardStats() {
    return this.request('/v1/dashboard/stats');
  }

  /**
   * Cases API
   */
  async getCases(params = {}) {
    const searchParams = new URLSearchParams(params).toString();
    const query = searchParams ? `?${searchParams}` : '';
    return this.request(`/v1/cases${query}`);
  }

  async getCaseById(id) {
    return this.request(`/v1/cases/${id}`);
  }

  async createCase(caseData) {
    return this.request('/v1/cases', {
      method: 'POST',
      body: JSON.stringify(caseData),
    });
  }

  async updateCase(caseId, payload, operator = 'Forensic Specialist') {
    return this.request(`/v1/cases/${caseId}?operator=${encodeURIComponent(operator)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Evidence Vault & Cryptographic Verification API
   */
  async getEvidence(caseId = null) {
    const endpoint = caseId ? `/v1/cases/${caseId}/evidence` : '/v1/evidence';
    return this.request(endpoint);
  }

  async uploadEvidence(caseId, formData) {
    return this.request(`/v1/cases/${caseId}/evidence`, {
      method: 'POST',
      body: formData,
    });
  }

  async verifyEvidence(evidenceId, operator = 'Forensic Examiner') {
    return this.request(`/v1/evidence/${evidenceId}/verify?operator=${encodeURIComponent(operator)}`, {
      method: 'POST',
    });
  }

  async getEvidenceMetadata(evidenceId) {
    return this.request(`/v1/evidence/${evidenceId}/metadata`);
  }

  /**
   * Security Log Analysis API
   */
  async analyzeLogs(caseId, formData) {
    return this.request(`/v1/cases/${caseId}/logs/analyze`, {
      method: 'POST',
      body: formData,
    });
  }

  async getCaseEvents(caseId, params = {}) {
    const searchParams = new URLSearchParams(params).toString();
    const query = searchParams ? `?${searchParams}` : '';
    return this.request(`/v1/cases/${caseId}/events${query}`);
  }

  /**
   * Unified Chronological Timeline API
   */
  async getTimeline(caseId, params = {}) {
    const searchParams = new URLSearchParams(params).toString();
    const query = searchParams ? `?${searchParams}` : '';
    return this.request(`/v1/cases/${caseId}/timeline${query}`);
  }

  /**
   * Forensic Reports & PDF Generator API
   */
  async getReportSummary(caseId) {
    return this.request(`/v1/cases/${caseId}/report/summary`);
  }

  async downloadReportPdf(caseId, caseNumber = 'Case', operator = 'Forensic Specialist') {
    const blob = await this.request(`/v1/cases/${caseId}/report/pdf?operator=${encodeURIComponent(operator)}`, {
      isBlob: true,
    });
    // Create temporary download link in browser
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Forensic_Report_${caseNumber}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    return true;
  }

  /**
   * Audit Trail API
   */
  async getAuditTrail(caseId = null) {
    const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : '';
    return this.request(`/v1/audit${query}`);
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
