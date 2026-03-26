/**
 * ParkM CSR Wizard — Configuration
 */
var ParkMConfig = {
  // Railway API base URL (no trailing slash)
  API_BASE_URL: "https://parkm-production.up.railway.app",

  // Custom field API names
  FIELDS: {
    AI_TAGS:               "cf_ai_tags",
    AI_CONFIDENCE:         "cf_ai_confidence",
    AI_URGENCY:            "cf_ai_urgency",
    AI_COMPLEXITY:         "cf_ai_complexity",
    AI_LANGUAGE:           "cf_ai_language",
    REQUIRES_REFUND:       "cf_requires_refund",
    REQUIRES_HUMAN_REVIEW: "cf_requires_human_review",
    LICENSE_PLATE:         "cf_license_plate",
    ROUTING_QUEUE:         "cf_routing_queue",
    AGENT_CORRECTED_TAGS:  "cf_agent_corrected_tags"
  },

  // Urgency badge styles
  URGENCY_STYLES: {
    high:   { bg: "#fdecea", text: "#c0392b", label: "HIGH" },
    medium: { bg: "#fff3e0", text: "#e67e22", label: "MEDIUM" },
    low:    { bg: "#e8f5e9", text: "#27ae60", label: "LOW" }
  },

  // Complexity badge styles
  COMPLEXITY_STYLES: {
    simple:   { bg: "#e8f5e9", text: "#27ae60" },
    moderate: { bg: "#fff3e0", text: "#e67e22" },
    complex:  { bg: "#fdecea", text: "#c0392b" }
  }
};
