// Lumara Configuration
// Update this file with your deployed backend URL

const LUMARA_CONFIG = {
    // Replace with your actual Render.com backend URL
    // Format: https://your-app-name.onrender.com
    BACKEND_URL: 'https://lumara-backend.onrender.com',
    
    // Alternative backend URLs for failover (optional)
    FALLBACK_URLS: [
        // 'https://backup-backend.railway.app'
    ],
    
    // API endpoints
    ENDPOINTS: {
        REFINE: '/api/refine',
        HEALTH: '/api/health'
    },
    
    // Wake up sleeping backend (for Render free tier)
    WAKE_UP_DELAY: 30000 // 30 seconds for cold start
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LUMARA_CONFIG;
}
