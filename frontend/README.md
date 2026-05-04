# Personal Podcast Generator - Frontend

Modern React + TypeScript frontend for generating personalized AI podcasts.

## Features

### User View
- **Interest Selection**: Tag-based input for selecting topics
- **Customization Panel**: Configure podcast length (Short/Medium/Long) and tone (Serious/Balanced/Casual)
- **Audio Player**: Custom player with:
  - Play/pause controls
  - Variable speed control (0.5x to 2x)
  - Progress bar with seek functionality
  - Audio waveform visualizer
  - Volume control with mute
  - Download functionality
- **Real-time Status Updates**: Polling mechanism for tracking podcast generation

### Admin Dashboard
- **KPI Cards**: Total Podcasts, Average Latency, Total API Cost, Success Rate
- **Volume Chart**: Interactive line chart showing daily podcast generation and latency
- **Health Monitor**: Table of recent tasks with status indicators
- **System Status**: Real-time monitoring of API, database, queue, and storage

## Tech Stack

- **React 18** with Hooks
- **TypeScript** for type safety
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Axios** for API requests
- **Lucide React** for icons
- **Vite** for fast development and building

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── AudioPlayer.tsx
│   ├── CustomizationPanel.tsx
│   ├── GenerateButton.tsx
│   ├── HealthMonitor.tsx
│   ├── InterestSelector.tsx
│   ├── KPICards.tsx
│   └── VolumeChart.tsx
├── pages/              # Route components
│   ├── Home.tsx
│   └── Admin.tsx
├── services/           # API client
│   └── api.ts
├── types/              # TypeScript definitions
│   ├── admin.ts
│   └── podcast.ts
├── App.tsx             # Router setup
├── index.css           # Global styles & animations
└── main.tsx            # Entry point
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your backend URL
# VITE_API_BASE_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:5173 in your browser
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Linting

```bash
# Run ESLint
npm run lint
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API endpoint | `http://localhost:8000` |

## API Integration

The frontend communicates with the backend through the `/api` endpoints:

- `POST /api/podcasts/generate` - Initiate podcast generation
- `GET /api/podcasts/:id/status` - Poll for generation status
- `GET /api/podcasts/:id/audio` - Download audio file
- `GET /api/admin/stats` - Fetch admin dashboard statistics

The API client includes:
- Automatic retry logic with exponential backoff
- Request/response interceptors for logging
- Error handling and parsing
- Polling utilities for async task tracking

## Key Components

### InterestSelector
Tag-based input with validation:
- Maximum 10 interests
- 2-50 character length validation
- Duplicate detection
- Real-time error feedback

### CustomizationPanel
Visual selection for:
- Length: Short (~5min), Medium (~10min), Long (~15min)
- Tone: Serious, Balanced, Casual

### AudioPlayer
Full-featured audio player:
- HTML5 audio with custom controls
- Waveform visualization (100 bars)
- Speed control (0.5x, 0.75x, 1x, 1.25x, 1.5x, 1.75x, 2x)
- Volume control with mute
- Download functionality

### Admin Dashboard Components

**KPICards**: Displays key metrics with color-coded icons
**VolumeChart**: Dual-axis line chart (Recharts) showing podcast count and latency
**HealthMonitor**: Real-time task status with filters and summaries

## Styling

Custom Tailwind CSS with:
- Gradient backgrounds
- Smooth animations (fade-in, scale-in, slide-in)
- Custom scrollbar styling
- Responsive design (mobile-first)
- Hover effects and transitions
- Focus states for accessibility

## Development Features

- **Hot Module Replacement** (HMR)
- **TypeScript strict mode** for type safety
- **Mock data** support for admin dashboard
- **ESLint** configuration for code quality
- **Responsive breakpoints** (sm, md, lg, xl)

## Performance Optimizations

- Code splitting with React Router
- Lazy loading for routes
- Memoized callbacks with `useCallback`
- Efficient re-rendering with proper state management
- Optimized bundle size with tree-shaking

## Accessibility

- Semantic HTML elements
- ARIA labels for controls
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

## Troubleshooting

### Build Errors

If you encounter TypeScript errors:
```bash
# Clear cache and reinstall
rm -rf node_modules dist
npm install
npm run build
```

### API Connection Issues

Ensure backend is running and VITE_API_BASE_URL is set correctly:
```bash
# Check backend status
curl http://localhost:8000/health
```

### Port Already in Use

Change the default port in `vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    port: 3000,
  },
});
```

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new components
3. Add proper prop types and interfaces
4. Include error handling
5. Write responsive, accessible UI
6. Test on multiple browsers

## License

MIT
