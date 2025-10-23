# Career Copilot Frontend

Modern Next.js frontend for the Career Copilot job application tracking system.

## Features

- **Modern Stack**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Responsive Design**: Mobile-first design that works on all devices
- **Job Management**: Add, edit, delete, and track job opportunities
- **Application Tracking**: Monitor application status and progress
- **Analytics Dashboard**: View key metrics and insights
- **User Authentication**: Secure login and registration
- **Real-time Updates**: Live data synchronization with backend

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend server running on http://localhost:8002

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local with your backend URL
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Home page
│   │   └── globals.css      # Global styles
│   ├── components/          # React components
│   │   ├── Navigation.tsx   # Main navigation
│   │   ├── Dashboard.tsx    # Analytics dashboard
│   │   ├── JobsPage.tsx     # Job management
│   │   ├── ApplicationsPage.tsx # Application tracking
│   │   ├── LoginForm.tsx    # Authentication
│   │   └── ...
│   └── lib/
│       └── api.ts           # API client and types
├── public/                  # Static assets
├── package.json
└── README.md
```

## Key Components

### Dashboard
- Key metrics overview
- Daily application goals
- Recent activity
- Status breakdown

### Job Management
- Add/edit job opportunities
- Tech stack tracking
- Source attribution
- Match scoring
- Bulk operations

### Application Tracking
- Status management
- Interview feedback
- Timeline tracking
- Notes and comments

### Analytics
- Performance metrics
- Success rates
- Conversion funnels
- Market insights

## API Integration

The frontend communicates with the FastAPI backend through a typed API client (`src/lib/api.ts`). All API calls are properly typed and include error handling.

### Key API Features:
- Authentication with JWT tokens
- Automatic token refresh
- Error handling and retry logic
- TypeScript interfaces for all data types

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

- TypeScript for type safety
- ESLint for code quality
- Prettier for formatting
- Tailwind CSS for styling

## Migration from Streamlit

This frontend replaces the previous Streamlit implementation with several improvements:

### Advantages over Streamlit:
- **Better Performance**: Faster loading and rendering
- **Modern UX**: Professional, responsive interface
- **Type Safety**: Full TypeScript support
- **Scalability**: Component-based architecture
- **SEO Friendly**: Server-side rendering support
- **Mobile Support**: Responsive design
- **Customization**: Full control over UI/UX

### Migrated Features:
- ✅ Job management with tech stack
- ✅ Application tracking
- ✅ Analytics dashboard
- ✅ User authentication
- ✅ Responsive navigation
- 🚧 Advanced analytics (in progress)
- 🚧 Recommendations engine (in progress)
- 🚧 Profile management (in progress)

## Deployment

### Production Build

```bash
npm run build
npm run start
```

### Environment Variables

- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL
- `NEXT_PUBLIC_APP_ENV` - Environment (development/production)

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Include proper error handling
4. Test on mobile and desktop
5. Update documentation

## Legacy Streamlit Frontend

The previous Streamlit frontend has been moved to `frontend-backup/` for reference. It contains:
- Interactive analytics dashboard
- Contract analysis features
- Security components
- Configuration files

These features will be gradually migrated to the new Next.js frontend.