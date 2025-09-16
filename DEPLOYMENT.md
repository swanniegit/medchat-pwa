# MedChat PWA - Fly.io Deployment Guide

## 🚀 Quick Deployment

### Prerequisites
1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Sign up/Login**: `fly auth signup` or `fly auth login`
3. **Git repository** with all project files

### Deploy to Fly.io

```bash
# 1. Initialize Fly app
fly apps create medchat-pwa --machines

# 2. Deploy the app
fly deploy

# 3. Set secrets (optional for now)
fly secrets set SECRET_KEY=$(openssl rand -hex 32)

# 4. Check deployment
fly status
fly logs
```

**🌍 Your app will be live at:** `https://medchat-pwa.fly.dev`

## 🔧 Configuration Details

### Fly.toml Highlights
- **Region**: Johannesburg (jnb) - South Africa
- **Memory**: 512MB (perfect for medical chat)
- **Auto-scaling**: Scales to 0 when inactive
- **HTTPS**: Automatic SSL certificates
- **Health checks**: `/health` endpoint monitoring

### Cost Estimate
- **Free tier**: Up to 3 shared CPU VMs
- **Light usage**: ~$5-15/month
- **Growing team**: ~$15-30/month

## 🏥 Medical Compliance Features

### Security
- ✅ **HTTPS/TLS encryption**
- ✅ **Security headers** (CSP, HSTS, etc.)
- ✅ **Input sanitization**
- ✅ **Rate limiting**
- ✅ **CORS restrictions**

### Data Protection
- ✅ **In-memory storage** (no persistent data in POC)
- ✅ **Message sanitization**
- ✅ **User validation**

## 🔍 Monitoring & Logs

```bash
# View live logs
fly logs

# Check app status
fly status

# Scale up/down
fly scale count 2  # 2 instances
fly scale count 1  # back to 1

# SSH into running app
fly ssh console
```

## 🚨 Troubleshooting

### Common Issues

**Build fails:**
```bash
fly doctor  # Check system
fly logs    # Check logs
```

**App not responding:**
```bash
fly status                    # Check health
fly apps restart medchat-pwa # Restart
```

**Database needed (future):**
```bash
fly postgres create --name medchat-db
fly postgres attach medchat-db
```

## 📈 Scaling for More Users

### Current Setup (POC)
- **Users**: Up to 100 concurrent
- **Storage**: In-memory (resets on restart)
- **Cost**: Free to $10/month

### Production Scaling
- **Add PostgreSQL**: `fly postgres create`
- **Add Redis**: `fly redis create`
- **Multiple regions**: `fly scale count 2 --region jnb,fra`

## 🔐 Environment Variables

Production secrets to set:
```bash
fly secrets set SECRET_KEY=your-production-secret
fly secrets set JWT_SECRET=your-jwt-secret
fly secrets set FRONTEND_URL=https://medchat-pwa.fly.dev
```

## 📱 Domain Setup (Optional)

```bash
fly domains create yourdomain.com
fly certs create yourdomain.com
```

## 🏥 Medical Team Onboarding

1. **Share URL**: `https://medchat-pwa.fly.dev`
2. **Demo accounts**: Create with department names
3. **Test features**:
   - Real-time messaging
   - Professional profiles
   - Multi-tab/device support

## 📊 Usage Monitoring

Fly.io provides built-in metrics:
- **Response times**
- **Memory usage**
- **Active connections**
- **Geographic distribution**

Perfect for tracking your medical team's usage patterns!

## 🆘 Support

- **Fly.io Docs**: https://fly.io/docs
- **Community**: https://community.fly.io
- **Status Page**: https://status.fly.io