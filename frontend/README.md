# World Cup Hot Topics Monitor - Frontend

React + TailwindCSS frontend for the World Cup Hot Topics Monitor.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **Routing**: React Router v6
- **HTTP Client**: Axios

## Project Structure

```
frontend/
├── src/
│   ├── components/   # React components
│   ├── pages/        # Page components
│   ├── services/     # API clients
│   ├── types/        # TypeScript types
│   ├── App.tsx       # Root component
│   └── main.tsx      # Entry point
├── public/           # Static assets
└── package.json      # Dependencies
```

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure API endpoint**:
   Edit `src/services/api.ts` to point to your backend URL (default: http://localhost:8000)

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

## Features

- **Discovery Feed**: Browse AI-curated hot topic cards
- **Channel Filtering**: Filter by category (转会传闻, 球队动态, etc.)
- **Detail Pages**: Click cards for detailed content with inline citations
- **Real-time Updates**: Polling service for new topic notifications
- **Responsive Design**: Mobile and desktop layouts

## Development

The frontend polls the backend API every 30 seconds for new content. Make sure the backend is running at http://localhost:8000 before starting the frontend.

## License

MIT
