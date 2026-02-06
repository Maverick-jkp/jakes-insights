// Test data for consistent E2E testing
// Sample posts for testing across languages

const SAMPLE_POSTS = {
  en: [
    '/ko/business/2026-02-03-부업-아이디어/',
    '/ko/business/2026-01-27-국세청장/',
    '/ko/business/2026-01-25-이재용/',
  ],
  ko: [
    '/ko/tech/2026-02-05-서울대-한예종-동시합격/',
    '/ko/society/2026-02-05-신설학교-개교/',
    '/ko/tech/2026-02-05-중등교사-전문성/',
  ],
  ja: [
    '/ja/society/2026-02-05-長野大学パワハラ/',
    '/ja/business/2026-02-03-副業アイデア/',
    '/ja/business/2026-01-27-鹿島建設/',
  ],
};

// Valid categories for validation
const VALID_CATEGORIES = [
  'tech',
  'business',
  'society',
  'entertainment',
  'sports'
];

// AI phrases to avoid (from quality_gate.py blacklist)
const AI_BLACKLIST = [
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
const SEO_PATTERNS = {
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
const PERFORMANCE_BUDGETS = {
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

module.exports = {
  SAMPLE_POSTS,
  VALID_CATEGORIES,
  AI_BLACKLIST,
  SEO_PATTERNS,
  PERFORMANCE_BUDGETS,
};
