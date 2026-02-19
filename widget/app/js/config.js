/**
 * ParkM CSR Wizard — Configuration
 */
var ParkMConfig = {
  // Railway API base URL (no trailing slash)
  API_BASE_URL: "https://parkm-production.up.railway.app",

  // Custom field API names (must match tagger.py lines 22-33)
  FIELDS: {
    AI_INTENT:             "cf_ai_intent",
    AI_CONFIDENCE:         "cf_ai_confidence",
    AI_URGENCY:            "cf_ai_urgency",
    AI_COMPLEXITY:         "cf_ai_complexity",
    AI_LANGUAGE:           "cf_ai_language",
    REQUIRES_REFUND:       "cf_requires_refund",
    REQUIRES_HUMAN_REVIEW: "cf_requires_human_review",
    LICENSE_PLATE:         "cf_license_plate",
    MOVE_OUT_DATE:         "cf_move_out_date",
    ROUTING_QUEUE:         "cf_routing_queue",
    AGENT_CORRECTED:       "cf_agent_corrected_intent"
  },

  // All 9 supported intents
  INTENTS: [
    "refund_request",
    "permit_cancellation",
    "account_update",
    "payment_issue",
    "permit_inquiry",
    "move_out",
    "technical_issue",
    "general_question",
    "unclear"
  ],

  // Intent display labels
  INTENT_LABELS: {
    refund_request:      "Refund Request",
    permit_cancellation: "Permit Cancellation",
    account_update:      "Account / Vehicle Update",
    payment_issue:       "Payment Issue",
    permit_inquiry:      "Permit Inquiry",
    move_out:            "Move-Out Notification",
    technical_issue:     "Technical Issue",
    general_question:    "General Question",
    unclear:             "Unclear / Needs Review"
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
