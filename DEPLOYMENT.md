# Zippie Payment App - Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Docker (optional)
- Git

### Local Development

1. **Install Dependencies**
   ```bash
   # Frontend
   npm install
   
   # Backend
   cd backend
   npm install
   ```

2. **Environment Setup**
   ```bash
   # Copy environment file
   cp backend/env.example backend/.env
   
   # Edit backend/.env with your configuration
   ```

3. **Start Development Servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   npm run dev
   
   # Terminal 2 - Frontend
   npm start
   ```

### Production Deployment

#### Option 1: Docker (Recommended)

1. **Build and Run with Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

2. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Health Check: http://localhost:5000/api/health

#### Option 2: Manual Deployment

1. **Build Frontend**
   ```bash
   npm run build:prod
   ```

2. **Start Backend**
   ```bash
   cd backend
   NODE_ENV=production npm start
   ```

3. **Serve Frontend**
   ```bash
   npx serve -s build -l 3000
   ```

## 🔧 Configuration

### Environment Variables

Create `backend/.env` with the following variables:

```env
PORT=5000
NODE_ENV=production
JWT_SECRET=your-super-secret-jwt-key-change-in-production
CORS_ORIGIN=http://localhost:3000
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

### Security Considerations

1. **Change JWT Secret**: Update `JWT_SECRET` in production
2. **HTTPS**: Use HTTPS in production
3. **CORS**: Configure `CORS_ORIGIN` for your domain
4. **Rate Limiting**: Adjust rate limits based on your needs

## 📊 Monitoring

### Health Checks
- Backend: `GET /api/health`
- Frontend: Available at root URL

### Logs
- Backend logs are output to console
- Use a process manager like PM2 for production
- Consider using a logging service like Winston

## 🛠️ Development Scripts

```bash
# Frontend
npm start              # Start development server
npm run build         # Build for production
npm run build:prod    # Build with production optimizations
npm test              # Run tests
npm run test:coverage # Run tests with coverage
npm run lint          # Lint code
npm run type-check    # TypeScript type checking

# Backend
cd backend
npm start             # Start production server
npm run dev          # Start development server with nodemon
```

## 🐳 Docker Commands

```bash
# Build image
docker build -t zippie-app .

# Run container
docker run -p 3000:3000 -p 5000:5000 zippie-app

# Docker Compose
docker-compose up -d          # Start services
docker-compose down           # Stop services
docker-compose logs -f        # View logs
docker-compose restart        # Restart services
```

## 🔒 Security Features

- **Helmet.js**: Security headers
- **CORS**: Cross-origin resource sharing
- **Rate Limiting**: API rate limiting
- **Input Validation**: Request validation
- **Error Boundaries**: React error handling
- **Compression**: Response compression

## 📱 Mobile Optimization

- Responsive design for mobile devices
- Touch-friendly interface
- Optimized for Zimbabwe payment systems
- Support for EcoCash, OneMoney, and bank transfers

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process using port
   lsof -ti:3000 | xargs kill -9
   lsof -ti:5000 | xargs kill -9
   ```

2. **Docker Issues**
   ```bash
   # Clean up Docker
   docker system prune -a
   docker-compose down -v
   ```

3. **Build Failures**
   ```bash
   # Clear cache and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

### Performance Optimization

1. **Frontend**
   - Code splitting implemented
   - Memoization for expensive operations
   - Error boundaries for graceful failures

2. **Backend**
   - Compression middleware
   - Rate limiting
   - Input validation
   - Graceful shutdown handling

## 📈 Production Checklist

- [ ] Environment variables configured
- [ ] JWT secret changed
- [ ] HTTPS enabled
- [ ] CORS configured for production domain
- [ ] Rate limiting configured
- [ ] Error monitoring setup
- [ ] Database configured (if using)
- [ ] Backup strategy implemented
- [ ] SSL certificates installed
- [ ] Domain configured

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Ensure all dependencies are installed
4. Verify environment configuration

## 📄 License

This project is licensed under the MIT License.
