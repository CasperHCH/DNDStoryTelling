# Synology NAS Deployment Checklist

## 📋 Pre-Deployment Testing Requirements

Based on the current test results and Synology DS718+ specifications, here's a comprehensive checklist to ensure stable production deployment:

## 🚨 Critical Issues to Fix Before Deployment

### 1. Database Migration Issues
- **Status**: ❌ FAILING - Alembic migration error
- **Issue**: `TypeError: EnvironmentContext.run_migrations() takes 1 positional argument but 2 were given`
- **Impact**: Database won't initialize properly on first deployment
- **Fix Required**: Update `alembic/env.py` to use correct async migration syntax

### 2. SECRET_KEY Validation
- **Status**: ❌ FAILING - Secret key too short for production
- **Issue**: Test secret key 'test_secret_key' only 15 chars, needs 32+
- **Impact**: Security vulnerability in production
- **Fix Required**: Generate proper 32+ character secret key for Synology

### 3. Database Tables Missing
- **Status**: ❌ FAILING - Tables not created after migration failure
- **Issue**: `relation "users" does not exist`
- **Impact**: Authentication and user management won't work
- **Fix Required**: Fix migration script first, then verify table creation

## 🧪 Required Pre-Deployment Tests

### Core Application Tests ✅
- [x] Basic app creation and configuration
- [x] Root endpoint functionality
- [x] Environment variable loading
- [x] Text upload functionality

### Database & Migration Tests ❌
- [ ] **Critical**: Fix Alembic migration script
- [ ] **Critical**: Verify database table creation
- [ ] **Critical**: Test user registration/login flow
- [ ] Test database connection pooling under load
- [ ] Verify PostgreSQL data persistence across container restarts

### Security Tests ❌
- [ ] **Critical**: Generate production-grade SECRET_KEY (32+ chars)
- [ ] **Critical**: Test JWT token generation/validation
- [ ] Verify password hashing with bcrypt
- [ ] Test CORS settings for Synology environment
- [ ] Verify SSL/TLS configuration (if using reverse proxy)

### Resource Constraint Tests (Synology DS718+)
- [ ] **Memory**: Test with 1GB memory limit
- [ ] **CPU**: Test with single CPU core constraint
- [ ] **Storage**: Verify persistent volume mounting
- [ ] **Network**: Test under limited bandwidth

### ARM64 Compatibility Tests
- [ ] **Critical**: Test on ARM64 architecture (if possible)
- [ ] Verify all Python packages work on ARM64
- [ ] Test audio processing (Whisper) on ARM architecture
- [ ] Verify PostgreSQL ARM64 compatibility

### Production Environment Tests
- [ ] Test with production environment variables
- [ ] Verify health check endpoints work correctly
- [ ] Test log file rotation and storage
- [ ] Verify backup and restore procedures

## 🔧 Specific Synology Tests

### Docker Container Tests
```bash
# Test resource limits
docker stats --no-stream

# Test memory pressure
docker exec -it <container> ps aux --sort=-%mem | head -10

# Test disk usage
docker exec -it <container> df -h
```

### Network Configuration Tests
- [ ] Test reverse proxy configuration (if using)
- [ ] Verify port accessibility (5000, 5432)
- [ ] Test external API calls (OpenAI, Confluence)
- [ ] Verify DNS resolution within containers

### Persistence Tests
- [ ] Verify uploads folder persistence
- [ ] Test database data survival across restarts
- [ ] Verify configuration persistence
- [ ] Test log file persistence

## 🚀 Deployment Validation Steps

### Pre-Deployment Setup
1. **Fix Critical Issues First**:
   ```bash
   # 1. Fix Alembic migration
   # 2. Generate proper SECRET_KEY
   # 3. Test database creation
   ```

2. **Environment Preparation**:
   ```bash
   # Copy docker-compose.synology.yml to Synology
   # Set production environment variables
   # Create necessary directories
   ```

3. **Resource Allocation**:
   ```bash
   # Verify 1GB memory available
   # Ensure sufficient disk space (5GB minimum)
   # Check CPU availability
   ```

### Post-Deployment Validation
1. **Container Health**:
   ```bash
   docker-compose -f docker-compose.synology.yml ps
   docker-compose -f docker-compose.synology.yml logs
   ```

2. **Application Functionality**:
   ```bash
   curl http://localhost:5000/health
   curl http://localhost:5000/
   ```

3. **Database Connectivity**:
   ```bash
   docker-compose exec web python -c "from app.models.database import get_db_session; print('DB OK')"
   ```

## ⚠️ Risk Assessment

### High Risk ❌
- **Database migrations**: Could fail on first deployment
- **Authentication**: Won't work without proper tables
- **Security**: Weak secret key in production

### Medium Risk ⚠️
- **Resource constraints**: May cause performance issues
- **ARM64 compatibility**: Some packages might not work
- **UI tests**: Playwright failures might indicate frontend issues

### Low Risk ✅
- **Basic functionality**: Core app works
- **Configuration**: Environment loading works
- **Health checks**: Basic endpoints functional

## 📝 Recommended Action Plan

### Phase 1: Fix Critical Issues (Required)
1. Fix Alembic migration script
2. Generate production SECRET_KEY
3. Test database table creation
4. Verify authentication flow

### Phase 2: Synology-Specific Testing (Recommended)
1. Test resource constraints locally
2. Verify ARM64 compatibility
3. Test persistent volumes
4. Performance testing under load

### Phase 3: Production Deployment (After Phases 1-2)
1. Deploy to Synology
2. Monitor logs and performance
3. Verify all functionality
4. Set up monitoring and alerts

## 🔍 Monitoring After Deployment

### Key Metrics to Watch
- Memory usage (should stay under 1GB)
- CPU utilization
- Database connection count
- Response times
- Error rates in logs

### Log Files to Monitor
- Application logs: `docker-compose logs web`
- Database logs: `docker-compose logs db`
- System logs: Check Synology DSM logs

## 🆘 Emergency Procedures

### If Deployment Fails
1. **Database Issues**:
   ```bash
   docker-compose down -v  # Remove volumes
   docker-compose up -d db  # Start fresh DB
   ```

2. **Resource Issues**:
   ```bash
   # Reduce memory limits in docker-compose.synology.yml
   # Scale down to minimal configuration
   ```

3. **Complete Rollback**:
   ```bash
   docker-compose down
   # Restore from backup
   ```

---

**Next Steps**: Fix the critical issues identified above before proceeding with Synology deployment. Focus on database migrations and security configuration first.