# WearWise — Frontend

React + Vite frontend for the WearWise AI Personal Fashion Stylist platform.

## Structure

```
WearWise/
└── frontend/
    ├── src/
    │   ├── api/          ← Backend API service layer
    │   ├── components/   ← Shared components
    │   ├── context/      ← Auth context
    │   ├── data/         ← Static collections data
    │   ├── pages/        ← All page components + CSS
    │   └── styles/       ← Global design system CSS
    ├── public/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── .env.example
```

## Quick Start

```bash
cd frontend

# Copy env file
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000

# Install
npm install

# Run
npm run dev
```

Frontend runs at **http://localhost:5173**

Requires the WearWise backend running at **http://localhost:8000**
