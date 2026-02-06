// Test data for consistent E2E testing
// Sample posts for testing across languages

export const SAMPLE_POSTS = {
  en: [
    '/en/entertainment/2026-02-04-daredevil/',
    '/en/tech/2026-02-04-amazon-down/',
    '/en/business/2026-02-03-passive-income-ideas-2026/',
  ],
  ko: [
    '/ko/entertainment/2026-02-05-신동엽/',
    '/ko/tech/2026-02-05-서울대-한예종-동시합격/',
    '/ko/society/2026-02-05-신설학교-개교/',
  ],
  ja: [
    '/ja/society/2026-02-05-長野大学パワハラ/',
    '/ja/tech/2026-02-04-日本製鉄/',
  ],
};

// Valid categories for validation
export const VALID_CATEGORIES = [
  'tech',
  'business',
  'society',
  'entertainment',
  'sports'
];

// AI phrases to avoid (from quality_gate.py blacklist)
export const AI_BLACKLIST = [
  'delve into',
  'navigating the landscape',
  "in today's fast-paced",
  "in today's world",
  'at the end of the day',
  'the fact of the matter',
  'as the old saying goes',
  'crucial to understand',
  'unparalleled insights',
  'game-changer',
];

// Expected meta tag patterns
export const SEO_PATTERNS = {
  description: {
    minLength: 120,
    maxLength: 160,
  },
  title: {
    minLength: 30,
    maxLength: 60,
  },
};

// Performance budgets (Core Web Vitals)
export const PERFORMANCE_BUDGETS = {
  lcp: {
    good: 2500,        // < 2.5s
    needsImprovement: 4000,  // 2.5-4.0s
  },
  fcp: {
    good: 1800,        // < 1.8s
    needsImprovement: 3000,  // 1.8-3.0s
  },
  cls: {
    good: 0.1,         // < 0.1
    needsImprovement: 0.25,  // 0.1-0.25
  },
};
