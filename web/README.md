# Algorand Sovereignty Analyzer - Web Frontend

The Next.js 16 frontend for the Algorand Sovereignty Analyzer, providing a modern React 19 interface for wallet analysis and sovereignty scoring.

## Quick Start

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Environment Configuration

Create `.env.local` in this directory:

```bash
# =============================================================================
# API Backend URL (Required)
# =============================================================================
# Points to your FastAPI backend

# Development (local backend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (Railway backend)
# NEXT_PUBLIC_API_URL=https://algo-sovereignty-api.up.railway.app
```

### NEXT_PUBLIC_API_URL Examples

| Scenario | Value |
|----------|-------|
| Local dev (backend on same machine) | `http://localhost:8000` |
| Local dev (backend on another machine) | `http://192.168.1.100:8000` |
| Staging (Railway preview) | `https://algo-staging.up.railway.app` |
| Production | `https://api.algosovereignty.com` |

**Note**: The `NEXT_PUBLIC_` prefix is required for browser access. Only use this for non-sensitive configuration.

## Project Structure

```
web/
├── app/                      # Next.js App Router pages
│   ├── page.tsx             # Landing page with wallet search
│   ├── analyze/             # Analysis results dashboard
│   │   └── page.tsx         # Main results page
│   ├── philosophy/          # Sovereignty Manifesto page
│   ├── training/            # Educational content
│   ├── about/               # About page
│   ├── network/             # Network sovereignty audit
│   ├── arbitrage/           # BTC arbitrage spotter
│   ├── gold-tracker/        # Gold miner metrics
│   ├── silver-tracker/      # Silver miner metrics
│   └── layout.tsx           # Root layout with providers
│
├── components/              # Reusable React components
│   ├── ui/                  # Shadcn/ui components
│   ├── LoadingState.tsx     # Content-aware skeletons
│   ├── ErrorAlert.tsx       # Error display with retry
│   ├── CoachingPanel.tsx    # AI advisor panel
│   ├── AssetBreakdown.tsx   # Category breakdown cards
│   └── SearchBar.tsx        # Wallet address input
│
├── lib/                     # Utilities and configuration
│   ├── api.ts              # Backend API client
│   ├── types.ts            # TypeScript interfaces
│   └── utils.ts            # Helper functions
│
├── public/                  # Static assets
└── styles/                  # Global styles (Tailwind)
```

## Key Features

### Wallet Analysis (`/analyze`)
- Enter any Algorand address
- View categorized assets (Hard Money, Algo, Dollars, Shitcoins)
- See sovereignty score and status
- AI-powered coaching recommendations

### Philosophy Page (`/philosophy`)
- Sovereignty Manifesto
- Six Paths to Sovereignty
- Network infrastructure audit explanation

### Training (`/training`)
- Educational content about hard money
- Sovereignty concepts explained

## Development

### Available Scripts

```bash
npm run dev      # Start development server (port 3000)
npm run build    # Create production build
npm run start    # Run production build
npm run lint     # Run ESLint
```

### Type Checking

```bash
# Full type check
npm run build

# Watch mode (IDE integration)
# TypeScript errors show in real-time
```

### Adding New Pages

1. Create directory under `app/`:
   ```bash
   mkdir app/new-page
   ```

2. Create `page.tsx`:
   ```tsx
   export default function NewPage() {
     return (
       <div className="container mx-auto px-4 py-12">
         <h1>New Page</h1>
       </div>
     )
   }
   ```

3. Page is automatically available at `/new-page`

### Using the API Client

```tsx
import { analyzeWallet, getCoachingAdvice } from '@/lib/api'

// In a component or server action
const result = await analyzeWallet(address, expenses)
const advice = await getCoachingAdvice(address, result)
```

## Deployment on Vercel

### Automatic Deployment

1. Push to GitHub
2. Connect repo in Vercel dashboard
3. Set root directory to `web`
4. Add environment variables
5. Deploy

### Environment Variables in Vercel

Navigate to Project Settings → Environment Variables:

| Name | Value | Environments |
|------|-------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://api.algosovereignty.com` | Production |
| `NEXT_PUBLIC_API_URL` | `https://staging-api.up.railway.app` | Preview |

### Build Settings

Vercel auto-detects Next.js:
- Framework: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

## Troubleshooting

### "Failed to fetch" errors

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. Check NEXT_PUBLIC_API_URL is correct:
   ```bash
   echo $NEXT_PUBLIC_API_URL
   ```

3. Verify CORS is configured on backend

### Hydration errors

Common with wallet connection libraries. Ensure:
1. Wallet providers wrap the app in `layout.tsx`
2. Use `'use client'` for interactive components

### Build failures

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

## Technology Stack

- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript 5** - Type safety
- **Tailwind CSS 4** - Styling
- **Shadcn/ui** - Component library
- **Recharts** - Charts and visualizations
- **@txnlab/use-wallet** - Algorand wallet connection

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Shadcn/ui Components](https://ui.shadcn.com/)
- [Algorand Developer Docs](https://developer.algorand.org/)
