# Database Query Tool - Frontend

React-based web application for the Database Query Tool, providing an intuitive interface for database management, SQL query execution, and natural language query generation.

## Features

- **Database Management**: Add, view, and manage PostgreSQL connections
- **Schema Browser**: Explore database structure with searchable tree view
- **SQL Query Editor**: Write and execute SQL with Monaco Editor
- **Natural Language Queries**: Generate SQL from plain English descriptions
- **Query Results**: Display results in paginated tables with metrics
- **Real-time Validation**: Instant feedback on SQL syntax and security

## Tech Stack

- **React**: 18.3+ with TypeScript
- **Vite**: 7.3.0 (build tool)
- **Refine**: 5.0.7 (framework for CRUD apps)
- **Ant Design**: 6.1.1 (UI components)
- **Monaco Editor**: SQL syntax highlighting and IntelliSense
- **Tailwind CSS**: 3.4+ (utility-first styling)
- **Axios**: HTTP client
- **React Router**: 7.1+ (navigation)

## Prerequisites

- Node.js 18+ or 20+
- npm 9+ or pnpm/yarn
- Backend server running on http://localhost:8000

## Installation

```bash
# Navigate to frontend directory
cd w2/db_query/frontend

# Install dependencies
npm install

# Or with pnpm
pnpm install

# Or with yarn
yarn install
```

## Configuration

The frontend is configured to connect to the backend at `http://localhost:8000/api/v1`.

To change the API base URL, edit `src/api/client.ts`:

```typescript
const client = axios.create({
  baseURL: 'http://your-backend-url/api/v1',
  timeout: 30000,
});
```

## Running the Application

### Development Mode

```bash
npm run dev

# Or with pnpm
pnpm dev

# Or with yarn
yarn dev
```

The application will start at `http://localhost:5173`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The build output will be in the `dist/` directory.

## Features Overview

### 1. Database Connections

**Location**: `/databases`

- Add new PostgreSQL database connections
- View list of all connections
- Set active database
- View schema metadata
- Delete connections

**Form Fields**:
- Name (unique identifier)
- Connection URL (postgresql://...)
- Active status (toggle)

### 2. Schema Browser

**Location**: `/schema`

- Browse database tables and views
- Search tables and columns
- View column details (type, nullable, PKs, FKs)
- Schema statistics dashboard
- Refresh schema metadata

**Features**:
- Real-time search with highlighting
- Expandable tree view
- Badge indicators for PKs and FKs
- Statistics: tables, views, columns, keys

### 3. Query Editor

**Location**: `/query`

- Write SQL queries with syntax highlighting
- Execute queries with Ctrl+Enter
- View results in paginated table
- Execution time and row count metrics
- Error display with validation messages

**Editor Features**:
- PostgreSQL syntax support
- Auto-completion
- Keyboard shortcuts
- Dark theme
- Line numbers

### 4. Natural Language Queries

**Location**: `/natural-query`

- Describe queries in plain English
- AI generates SQL with schema context
- Review and edit generated SQL
- Approve/reject workflow
- Execute after approval

**Workflow**:
1. Select database
2. Enter natural language query
3. Review generated SQL and explanation
4. Edit if needed
5. Approve and execute
6. View results

## Project Structure

```
frontend/
├── public/                  # Static assets
├── src/
│   ├── main.tsx            # Application entry point
│   ├── App.tsx             # Main app with routing
│   ├── index.css           # Global styles with Tailwind
│   ├── api/
│   │   ├── client.ts       # Axios instance
│   │   └── dataProvider.ts # Refine data provider
│   ├── components/
│   │   ├── ConnectionForm.tsx      # Database connection form
│   │   ├── SchemaTree.tsx          # Schema tree viewer
│   │   ├── SqlEditor.tsx           # Monaco SQL editor
│   │   ├── ResultsTable.tsx        # Query results table
│   │   ├── SqlApproval.tsx         # SQL approval workflow
│   │   ├── TagBadge.tsx            # Tag display component
│   │   └── ui/                     # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       ├── select.tsx
│   │       └── ...
│   ├── pages/
│   │   ├── DatabaseList.tsx        # Database management page
│   │   ├── QueryEditor.tsx         # SQL query page
│   │   ├── NaturalQuery.tsx        # Natural language page
│   │   └── SchemaBrowser.tsx       # Schema exploration page
│   ├── hooks/
│   │   ├── useActiveDb.ts          # Active database state
│   │   └── useQuery.ts             # Query execution hook
│   ├── types/
│   │   ├── database.ts             # Database types
│   │   ├── schema.ts               # Schema types
│   │   └── query.ts                # Query types
│   └── lib/
│       ├── api.ts                  # API functions
│       ├── types.ts                # Shared types
│       ├── colors.ts               # Color utilities
│       └── utils.ts                # Helper functions
├── components.json          # shadcn/ui config
├── tailwind.config.js       # Tailwind configuration
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite configuration
├── package.json             # Dependencies
└── README.md                # This file
```

## Navigation Menu

- **Databases** (🗄️) - Manage database connections
- **Schema Browser** (🔍) - Explore database structure
- **Query Editor** (</>) - Write and execute SQL
- **Natural Language** (💡) - AI-assisted queries

## Keyboard Shortcuts

- **Ctrl+Enter** / **Cmd+Enter**: Execute query (in editors)
- **Escape**: Close dialogs
- **Tab**: Navigate form fields

## Type Safety

The application uses TypeScript strict mode with full type coverage:

```typescript
// Example: Query response type
interface QueryResponse {
  sql: string;
  rows: Record<string, any>[];
  rowCount: number;
  executionTimeMs: number;
  columns: string[];
}
```

All API responses are typed and validated.

## Styling

### Tailwind CSS

Utility-first CSS framework for rapid UI development:

```tsx
<div className="flex items-center justify-between p-4 bg-blue-50">
  <span className="text-lg font-bold">Query Results</span>
</div>
```

### Ant Design

Component library for consistent UI:

```tsx
import { Button, Table, Card } from 'antd';

<Card title="Results">
  <Table dataSource={data} columns={columns} />
</Card>
```

## Error Handling

### API Errors

```typescript
try {
  const response = await client.post('/query', { sql });
  setData(response.data);
} catch (err: any) {
  const errorMsg = err.response?.data?.detail || 'Query failed';
  message.error(errorMsg);
}
```

### Validation Errors

- SQL syntax errors highlighted
- Form validation with Ant Design
- Real-time feedback
- Clear error messages

## Development

### Running Tests

```bash
npm run test

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Code Quality

```bash
# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run format
```

### Building

```bash
# Production build
npm run build

# Analyze bundle
npm run build -- --mode analyze
```

## Environment Variables

Create `.env.local` for local overrides:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Database Query Tool
```

Access in code:

```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Backend Connection Issues

```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Check CORS configuration in backend
```

### Monaco Editor Not Loading

```bash
# Clear cache
rm -rf node_modules/.vite

# Reinstall
npm install
```

### Build Errors

```bash
# Clear build cache
rm -rf dist node_modules/.vite

# Reinstall dependencies
npm install

# Rebuild
npm run build
```

### TypeScript Errors

```bash
# Check types
npm run type-check

# Regenerate types if needed
npm run codegen
```

## Performance Optimization

### Code Splitting

Routes are lazy-loaded automatically by Vite:

```typescript
const DatabaseList = lazy(() => import('./pages/DatabaseList'));
```

### Bundle Analysis

```bash
npm run build -- --mode analyze
```

### Production Optimizations

- Minification (Terser)
- Tree shaking
- CSS purging (Tailwind)
- Asset optimization
- Gzip compression

## Deployment

### Static Hosting (Vercel, Netlify)

```bash
npm run build
# Upload dist/ directory
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

### Environment Configuration

Set API URL for production:

```typescript
// src/api/client.ts
const baseURL = import.meta.env.PROD
  ? 'https://api.example.com/api/v1'
  : 'http://localhost:8000/api/v1';
```

## Contributing

1. Follow TypeScript strict mode
2. Use functional components with hooks
3. Follow Ant Design design patterns
4. Write tests for new features
5. Update types when changing APIs

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus management
- Screen reader support

## License

MIT License - see LICENSE file for details

## Support

For issues:
- Check browser console for errors
- Verify backend connection
- Review API documentation
- Test with simple queries first
