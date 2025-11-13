# Clinical Trial Analytics Platform - Frontend

Modern React + TypeScript frontend for the Synthetic Medical Data Generation platform.

## 🚀 Tech Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **Charts**: Recharts
- **State Management**: React Context API

## 📋 Prerequisites

- Node.js 18+
- npm or yarn
- Backend services running (see main project README)

## 🛠️ Installation

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` to configure backend service URLs (defaults to localhost):
```env
VITE_DATA_GEN_URL=http://localhost:8002
VITE_ANALYTICS_URL=http://localhost:8003
VITE_EDC_URL=http://localhost:8004
VITE_SECURITY_URL=http://localhost:8005
VITE_QUALITY_URL=http://localhost:8006
```

## 🏃 Running the Application

### Development Mode
```bash
npm run dev
```
Opens at http://localhost:3000

### Production Build
```bash
npm run build
npm run preview
```

## 📱 Features

### 1. **Authentication**
- User login and registration
- JWT token-based authentication
- Role-based access control (admin, researcher, viewer)
- Secure session management

### 2. **Dashboard**
- Overview of studies, subjects, and generated data
- Quick action cards
- System health monitoring
- Recent activity tracking

### 3. **Data Generation**
- **MVN Method**: Multivariate Normal generation (~29K records/sec)
- **Bootstrap Method**: Resampling with jitter (~140K records/sec)
- **Rules Method**: Deterministic business-rule generation (~80K records/sec)
- **LLM Method**: OpenAI GPT-4o-mini powered generation (~70 records/sec)
- Real-time generation with progress indicators
- CSV download functionality
- Data preview tables

### 4. **Analytics & Quality**
- Week-12 statistical analysis
- Treatment effect calculations
- Comprehensive quality assessment:
  - Wasserstein distances
  - RMSE by column
  - Correlation preservation
  - K-NN imputation scores
  - Euclidean distance metrics
- Quality score badges (Excellent/Good/Needs Improvement)

### 5. **Study Management**
- Create and manage clinical trials
- Import synthetic data into studies
- Subject enrollment tracking
- Study status monitoring

### 6. **Settings**
- User profile management
- API endpoint configuration
- Account actions

## 🎨 Design System

The application follows Material Design 3 principles with custom design tokens:

### Color Tokens
- **Primary**: Purple (#6750A4)
- **Secondary**: Gray tones
- **Semantic**: Success, Warning, Error, Info
- **Surface**: 5 elevation levels
- **Chart**: 5 distinct colors for data visualization

### Typography
- Font: System UI stack (optimized for each OS)
- Sizes: xs, sm, base, lg, xl, 2xl, 3xl
- Weights: normal (400), medium (500), semibold (600)

### Components
All UI components are built with:
- **Radix UI** primitives for accessibility
- **Tailwind CSS** utility classes for styling
- **CVA** (class-variance-authority) for variant management
- Full keyboard navigation support
- ARIA attributes

## 📂 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Primitive UI components (Button, Card, Input, etc.)
│   │   ├── layout/          # Layout components (TopAppBar, NavigationRail)
│   │   └── screens/         # Page components (Dashboard, DataGeneration, etc.)
│   ├── hooks/               # Custom React hooks (useAuth)
│   ├── services/            # API service layer
│   ├── types/               # TypeScript type definitions
│   ├── lib/                 # Utility functions (cn helper)
│   ├── App.tsx              # Main app component with routing
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles and design tokens
├── public/                  # Static assets
├── .env                     # Environment variables
├── tailwind.config.js       # Tailwind configuration
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite configuration
└── package.json             # Dependencies
```

## 🔌 API Integration

The frontend connects to 5 backend microservices:

### 1. Data Generation Service (8002)
```typescript
import { dataGenerationApi } from '@/services/api';

// Generate synthetic data
const response = await dataGenerationApi.generateMVN({
  n_per_arm: 50,
  target_effect: -5.0,
});
```

### 2. Analytics Service (8003)
```typescript
import { analyticsApi } from '@/services/api';

// Get Week-12 statistics
const stats = await analyticsApi.getWeek12Stats({
  vitals_data: generatedData,
});
```

### 3. EDC Service (8004)
```typescript
import { edcApi } from '@/services/api';

// Create a study
const study = await edcApi.createStudy({
  study_name: "Hypertension Phase 3",
  indication: "Hypertension",
  phase: "Phase 3",
  sponsor: "PharmaCo Inc",
  start_date: "2025-01-01",
});
```

### 4. Security Service (8005)
```typescript
import { authApi } from '@/services/api';

// Login
const { access_token, user } = await authApi.login({
  username: "researcher",
  password: "password",
});
```

### 5. Quality Service (8006)
```typescript
import { qualityApi } from '@/services/api';

// Validate vitals data
const validation = await qualityApi.validateVitals(vitalsData);
```

## 🧪 Default Login Credentials

For testing purposes, you may need to register a new user or use existing backend users:

**Registration**: Use the "Sign up" option on the login screen

**Example User**:
- Username: `researcher`
- Password: `password123`
- Role: `researcher`

## 🔧 Development

### Type Checking
```bash
npm run lint
```

### Build for Production
```bash
npm run build
```

Build output will be in `dist/` directory.

## 📊 Performance

- **Initial Load**: ~262 KB (gzipped: ~80 KB)
- **CSS**: ~7 KB (gzipped: ~2 KB)
- **Build Time**: ~1 second
- **Hot Module Replacement**: Instant updates during development

## 🎯 Key Features Implementation

### Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Navigation adapts to screen size
- Tables scroll horizontally on mobile

### Dark Mode Ready
- CSS custom properties support dark mode
- Toggle can be added in Settings
- All components support dark/light themes

### Accessibility
- Full keyboard navigation
- Screen reader support (ARIA labels)
- Focus visible states
- Semantic HTML
- Color contrast compliance (WCAG AA)

## 🐛 Troubleshooting

### Backend Connection Issues
If you see connection errors:
1. Ensure all backend services are running
2. Check `.env` file for correct URLs
3. Verify CORS is enabled on backend services

### Build Errors
```bash
# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Type Errors
```bash
# Regenerate TypeScript types
npm run build
```

## 📚 Additional Documentation

- **Backend API Reference**: See `../CLAUDE.md`
- **Design System Guide**: See `../../272/.claude/FIGMA_DESIGN_SYSTEM_RULES.md`
- **Component Library**: Run dev server and explore UI components

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Test thoroughly
4. Create a pull request

## 📄 License

See main project LICENSE file.

## 🔗 Related Documentation

- [Backend Implementation](../CLAUDE.md)
- [Scaling Guide](../SCALING_TO_MILLIONS_GUIDE.md)
- [Dashboard Summary](../DASHBOARD_SUMMARY.md)
- [Field Comparison](../FIELD_COMPARISON_SUMMARY.md)

---

**Built with** ❤️ **using React + TypeScript + Tailwind CSS + shadcn/ui**
