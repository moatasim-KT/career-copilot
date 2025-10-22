# Career Co-Pilot Deployment Guide

This comprehensive guide covers production deployment of the Career Co-Pilot system, including database migration, SMTP configuration, and security best practices.

## Table of Contents

1. [Production Environment Setup](#production-environment-setup)
2. [PostgreSQL Migration Instructions](#postgresql-migration-instructions)
3. [SMTP Configuration Examples](#smtp-configuration-examples)
4. [Security Checklist](#security-checklist)
5. [Deployment Options](#deployment-options)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Production Environment Setup

### Prerequisites

- **Server Requirements:**
  - Linux server (Ubuntu 20.04+ recommended)
  - Python 3.11+
  - PostgreSQL 13+
  - Nginx (for reverse proxy)
  - SSL certificate (Let's Encrypt recommended)
  - Minimum 2GB RAM, 20GB storage

- **Domain and DNS:**
  - Registered domain name
  - DNS A records pointing to your server
  - SSL certificate configured

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nginx postgresql postgresql-contrib redis-server supervisor git curl

# Create application user
sudo useradd -m -s /bin/bash career-copilot
sudo usermod -aG sudo career-copilot

# Create application directory
sudo mkdir -p /opt/career-copilot
sudo chown career-copilot:career-copilot /opt/career-copilot
```

### 2. Application Deployment

```bash
# Switch to application user
sudo su - career-copilot

# Clone repository
cd /opt/career-copilot
git clone <your-repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -U pip
pip install .[all]

# Create necessary directories
mkdir -p logs data/backups
```

### 3. Environment Configuration

```bash
# Copy and configure environment file
cp backend/.env.example backend/.env

# Edit configuration (see SMTP Configuration section below)
nano backend/.env
```

**Critical Production Settings:**

```bash
# Production environment
ENVIRONMENT=production
DEBUG=False
API_HOST=0.0.0.0
API_PORT=8002

# Database (configured in PostgreSQL section)
DATABASE_URL=postgresql://career_copilot:your_secure_password@localhost:5432/career_copilot_prod

# Security (CRITICAL - generate secure keys)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS (adjust for your domain)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Scheduler and automation
ENABLE_SCHEDULER=true
ENABLE_JOB_SCRAPING=true

# Logging
LOG_LEVEL=INFO
```

## PostgreSQL Migration Instructions

### 1. PostgreSQL Installation and Setup

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Secure PostgreSQL installation
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_postgres_admin_password';"
```

### 2. Database and User Creation

```bash
# Connect as postgres user
sudo -u postgres psql

-- Create production database and user
CREATE DATABASE career_copilot_prod;
CREATE USER career_copilot WITH ENCRYPTED PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE career_copilot_prod TO career_copilot;
ALTER USER career_copilot CREATEDB;

-- Exit PostgreSQL
\q
```

### 3. Database Migration from SQLite (if applicable)

If migrating from SQLite development database:

```bash
# Activate virtual environment
source /opt/career-copilot/venv/bin/activate
cd /opt/career-copilot

# Export data from SQLite (create migration script)
cat > migrate_to_postgres.py << 'EOF'
#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Add backend to path
sys.path.append('backend')

from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.database import Base

def migrate_data():
    # Source (SQLite) and target (PostgreSQL) connections
    sqlite_url = "sqlite:///backend/data/career_copilot.db"
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    print("Starting migration from SQLite to PostgreSQL...")
    
    # Create engines
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)
    
    # Create all tables in PostgreSQL
    Base.metadata.create_all(postgres_engine)
    
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Migrate users
        users = sqlite_session.query(User).all()
        for user in users:
            postgres_session.merge(user)
        print(f"Migrated {len(users)} users")
        
        # Migrate jobs
        jobs = sqlite_session.query(Job).all()
        for job in jobs:
            postgres_session.merge(job)
        print(f"Migrated {len(jobs)} jobs")
        
        # Migrate applications
        applications = sqlite_session.query(Application).all()
        for application in applications:
            postgres_session.merge(application)
        print(f"Migrated {len(applications)} applications")
        
        postgres_session.commit()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        postgres_session.rollback()
        print(f"Migration failed: {e}")
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    migrate_data()
EOF

# Make executable and run migration
chmod +x migrate_to_postgres.py
python migrate_to_postgres.py
```

### 4. Initialize Fresh Database

For new installations:

```bash
# Activate virtual environment
source /opt/career-copilot/venv/bin/activate
cd /opt/career-copilot/backend

# Run database initialization
python -c "
from app.core.database import engine, Base
from app.models import user, job, application
Base.metadata.create_all(engine)
print('Database tables created successfully')
"

# Run Alembic migrations
alembic upgrade head

# Optional: Seed with sample data
python scripts/seed_data.py
```

### 5. PostgreSQL Performance Tuning

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf

# Apply production settings (adjust based on your server specs)
# Copy from deployment/postgres/postgresql.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## SMTP Configuration Examples

### Gmail Configuration

```bash
# In backend/.env
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@your-domain.com
```

**Gmail Setup Steps:**
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the generated password (not your regular password)

### SendGrid Configuration

```bash
# Option 1: Using SendGrid API (recommended)
SENDGRID_API_KEY=SG.your-sendgrid-api-key

# Option 2: Using SendGrid SMTP
SMTP_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@your-domain.com
```

**SendGrid Setup Steps:**
1. Create account at https://sendgrid.com
2. Verify your sender domain
3. Create API key with Mail Send permissions
4. Configure DNS records for domain authentication

### Office 365 Configuration

```bash
SMTP_ENABLED=true
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

### Custom SMTP Server

```bash
SMTP_ENABLED=true
SMTP_HOST=mail.your-domain.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@your-domain.com
```

### Testing Email Configuration

```bash
# Test email configuration
cd /opt/career-copilot
source venv/bin/activate

python -c "
from backend.app.services.notification_service import NotificationService
from backend.app.core.config import get_settings

settings = get_settings()
notification_service = NotificationService(settings)

# Test email
result = notification_service._send_email(
    to_email='test@example.com',
    subject='Test Email',
    html_content='<h1>Test successful!</h1>',
    text_content='Test successful!'
)
print('Email test result:', result)
"
```

## Security Checklist

### 1. Server Security

- [ ] **Firewall Configuration**
  ```bash
  # Configure UFW firewall
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow ssh
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```

- [ ] **SSH Hardening**
  ```bash
  # Edit SSH configuration
  sudo nano /etc/ssh/sshd_config
  
  # Recommended settings:
  # PermitRootLogin no
  # PasswordAuthentication no
  # PubkeyAuthentication yes
  # Port 2222  # Change default port
  
  sudo systemctl restart ssh
  ```

- [ ] **Automatic Security Updates**
  ```bash
  sudo apt install unattended-upgrades
  sudo dpkg-reconfigure -plow unattended-upgrades
  ```

### 2. Application Security

- [ ] **Environment Variables**
  - [ ] JWT_SECRET_KEY is cryptographically secure (32+ characters)
  - [ ] Database passwords are strong and unique
  - [ ] API keys are properly secured
  - [ ] DEBUG=False in production
  - [ ] Environment file permissions: `chmod 600 backend/.env`

- [ ] **Database Security**
  ```bash
  # Secure PostgreSQL
  sudo nano /etc/postgresql/13/main/pg_hba.conf
  
  # Ensure only local connections allowed:
  # local   all             all                                     md5
  # host    all             all             127.0.0.1/32            md5
  
  sudo systemctl restart postgresql
  ```

- [ ] **SSL/TLS Configuration**
  ```bash
  # Install Certbot for Let's Encrypt
  sudo apt install certbot python3-certbot-nginx
  
  # Obtain SSL certificate
  sudo certbot --nginx -d your-domain.com -d www.your-domain.com
  
  # Auto-renewal
  sudo crontab -e
  # Add: 0 12 * * * /usr/bin/certbot renew --quiet
  ```

### 3. Nginx Security Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/career-copilot

# Use configuration from deployment/nginx/nginx.conf
# Then enable site:
sudo ln -s /etc/nginx/sites-available/career-copilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Application Monitoring

- [ ] **Log Monitoring**
  ```bash
  # Set up log rotation
  sudo nano /etc/logrotate.d/career-copilot
  
  /opt/career-copilot/logs/*.log {
      daily
      missingok
      rotate 52
      compress
      delaycompress
      notifempty
      create 644 career-copilot career-copilot
  }
  ```

- [ ] **Health Check Monitoring**
  ```bash
  # Create health check script
  cat > /opt/career-copilot/health_check.sh << 'EOF'
  #!/bin/bash
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/api/v1/health)
  if [ $response -eq 200 ]; then
      echo "$(date): Health check passed"
  else
      echo "$(date): Health check failed with code $response"
      # Add alerting logic here
  fi
  EOF
  
  chmod +x /opt/career-copilot/health_check.sh
  
  # Add to crontab
  crontab -e
  # Add: */5 * * * * /opt/career-copilot/health_check.sh >> /opt/career-copilot/logs/health.log
  ```

### 5. Backup Strategy

- [ ] **Database Backups**
  ```bash
  # Create backup script
  cat > /opt/career-copilot/backup_db.sh << 'EOF'
  #!/bin/bash
  BACKUP_DIR="/opt/career-copilot/data/backups"
  DATE=$(date +%Y%m%d_%H%M%S)
  
  # Create backup
  pg_dump -h localhost -U career_copilot career_copilot_prod > $BACKUP_DIR/backup_$DATE.sql
  
  # Compress backup
  gzip $BACKUP_DIR/backup_$DATE.sql
  
  # Remove backups older than 30 days
  find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
  
  echo "$(date): Database backup completed: backup_$DATE.sql.gz"
  EOF
  
  chmod +x /opt/career-copilot/backup_db.sh
  
  # Schedule daily backups
  crontab -e
  # Add: 0 2 * * * /opt/career-copilot/backup_db.sh >> /opt/career-copilot/logs/backup.log
  ```

## Deployment Options

### Option 1: Cloud Deployment (Render + Streamlit Cloud)

**Backend on Render:**
1. Connect GitHub repository to Render
2. Use provided `render.yaml` configuration
3. Set environment variables in Render dashboard
4. Deploy automatically on git push

**Frontend on Streamlit Cloud:**
1. Connect GitHub repository to Streamlit Cloud
2. Set main file path to `frontend/app.py`
3. Configure `BACKEND_URL` secret
4. Deploy automatically on git push

### Option 2: VPS Deployment

**Process Manager with Supervisor:**

```bash
# Install supervisor
sudo apt install supervisor

# Create supervisor configuration
sudo nano /etc/supervisor/conf.d/career-copilot.conf

[program:career-copilot-backend]
command=/opt/career-copilot/venv/bin/gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8002
directory=/opt/career-copilot
user=career-copilot
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/career-copilot/logs/backend.log

[program:career-copilot-frontend]
command=/opt/career-copilot/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1
directory=/opt/career-copilot
user=career-copilot
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/career-copilot/logs/frontend.log

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### Option 3: Docker Deployment

```bash
# Build and run with Docker Compose
cd /opt/career-copilot
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use the deployment script
./deployment/scripts/deploy-docker.sh production
```

## Monitoring and Maintenance

### 1. Application Monitoring

```bash
# Check application status
sudo supervisorctl status

# View logs
tail -f /opt/career-copilot/logs/backend.log
tail -f /opt/career-copilot/logs/frontend.log

# Check health endpoint
curl http://localhost:8002/api/v1/health
```

### 2. Database Monitoring

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Monitor database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('career_copilot_prod'));"
```

### 3. Performance Monitoring

```bash
# Monitor system resources
htop
df -h
free -h

# Monitor application performance
curl -s http://localhost:8002/api/v1/health | jq .

# Check Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### 4. Maintenance Tasks

**Weekly Tasks:**
- Review application logs for errors
- Check disk space usage
- Verify backup integrity
- Update system packages

**Monthly Tasks:**
- Review security logs
- Update application dependencies
- Performance optimization review
- SSL certificate renewal check

## Troubleshooting

### Common Issues

**1. Application Won't Start**
```bash
# Check logs
tail -f /opt/career-copilot/logs/backend.log

# Common causes:
# - Database connection issues
# - Missing environment variables
# - Port conflicts
# - Permission issues
```

**2. Database Connection Errors**
```bash
# Test database connection
sudo -u postgres psql -c "SELECT version();"

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Verify connection string
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('Database connection successful')
"
```

**3. Email Not Sending**
```bash
# Test SMTP configuration
python -c "
import smtplib
from email.mime.text import MIMEText

# Test connection (adjust settings)
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('SMTP connection successful')
server.quit()
"
```

**4. High Memory Usage**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Optimize if needed:
# - Reduce Gunicorn workers
# - Implement caching
# - Database query optimization
```

**5. SSL Certificate Issues**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --dry-run

# Check Nginx SSL configuration
sudo nginx -t
```

### Emergency Procedures

**1. Service Recovery**
```bash
# Restart all services
sudo supervisorctl restart all
sudo systemctl restart nginx
sudo systemctl restart postgresql

# Check service status
sudo supervisorctl status
sudo systemctl status nginx postgresql
```

**2. Database Recovery**
```bash
# Restore from backup
gunzip /opt/career-copilot/data/backups/backup_YYYYMMDD_HHMMSS.sql.gz
sudo -u postgres psql career_copilot_prod < backup_YYYYMMDD_HHMMSS.sql
```

**3. Rollback Deployment**
```bash
# Revert to previous version
cd /opt/career-copilot
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>
sudo supervisorctl restart all
```

### Support and Maintenance

- **Log Locations:**
  - Application: `/opt/career-copilot/logs/`
  - Nginx: `/var/log/nginx/`
  - PostgreSQL: `/var/log/postgresql/`
  - System: `/var/log/syslog`

- **Configuration Files:**
  - Application: `/opt/career-copilot/backend/.env`
  - Nginx: `/etc/nginx/sites-available/career-copilot`
  - PostgreSQL: `/etc/postgresql/13/main/postgresql.conf`
  - Supervisor: `/etc/supervisor/conf.d/career-copilot.conf`

- **Important Commands:**
  ```bash
  # Service management
  sudo supervisorctl status|start|stop|restart <service>
  sudo systemctl status|start|stop|restart <service>
  
  # Log monitoring
  tail -f /opt/career-copilot/logs/*.log
  journalctl -u <service> -f
  
  # Health checks
  curl http://localhost:8002/api/v1/health
  ```

This deployment guide provides comprehensive instructions for setting up Career Co-Pilot in production environments with proper security, monitoring, and maintenance procedures.