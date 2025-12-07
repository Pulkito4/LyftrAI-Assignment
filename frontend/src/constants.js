// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
export const API_ENDPOINTS = {
  SCRAPE: '/scrape',
  HEALTH: '/healthz',
};

// Interaction Strategies
export const INTERACTION_STRATEGIES = [
  { value: 'auto', label: 'Auto (Smart Detection)' },
  { value: 'tabs', label: 'Tabs Only' },
  { value: 'load_more', label: 'Load More Buttons' },
  { value: 'scroll', label: 'Infinite Scroll' },
  { value: 'pagination', label: 'Pagination' },
  { value: 'all', label: 'All Strategies' },
];

// Section Type Icons (lucide-react)
export const SECTION_TYPE_ICONS = {
  hero: 'Target',
  nav: 'Navigation',
  footer: 'FileText',
  pricing: 'DollarSign',
  faq: 'HelpCircle',
  list: 'List',
  grid: 'Grid',
  section: 'FileText',
  unknown: 'Circle',
};

// UI Constants
export const MAX_ITEMS_TO_DISPLAY = {
  HEADINGS: 5,
  LINKS: 5,
  IMAGES: 4,
};

export const TEXT_PREVIEW_LENGTH = 300;

// Timeouts
export const SCRAPE_TIMEOUT_MESSAGE = 'Scraping in progress... This may take up to 60 seconds.';

// Download Settings
export const DOWNLOAD_FILE_PREFIX = 'scrape-';
export const DOWNLOAD_FILE_EXTENSION = '.json';
