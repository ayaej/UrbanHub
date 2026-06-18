# n8n Workflows - UrbanHub Automation

## 📋 Workflows disponibles

### 1. urbanhub_daily_pipeline.json
**Exécution quotidienne du pipeline complet**

```
SCHEDULE: Every day at 2:00 AM
├── [1] Cron Trigger (Daily at 2 AM)
├── [2] Execute Python Pipeline
│   └── Command: python run_pipeline.py --skip-download
├── [3] Log Execution to PostgreSQL
│   └── INSERT INTO pipeline_runs
├── [4] Verify MinIO Health
│   └── GET http://minio:9000/health
└── [5] Send Email Notification
    └── Admin alert with stats
```

**Configuration**:
```json
{
  "trigger": "cron",
  "schedule": "0 2 * * *",  // 2:00 AM daily
  "tasks": [
    "execute_pipeline",
    "log_to_postgres",
    "verify_minio",
    "send_notification"
  ]
}
```

---

## 🔧 Installation & Setup

### Importer un workflow

```bash
# 1. Accédez à n8n
http://localhost:5678

# 2. Menu: Workflows → Import
# 3. Upload: workflows/urbanhub_daily_pipeline.json

# OU via API:
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @workflows/urbanhub_daily_pipeline.json
```

### Configurer Credentials

#### PostgreSQL

```
Name: PostgreSQL - urbanhub
Type: PostgreSQL
Host: postgres (ou localhost)
Port: 5432
Database: urbanhub
User: urbanhub_user
Password: urbanhub_password
```

#### SSH (pour execute_command)

```
Name: SSH - Docker
Type: SSH
Host: localhost (ou docker hostname)
Port: 22
Username: root
Private Key: [si password auth]
Password: [si key auth]
```

#### HTTP (pour MinIO health check)

```
Type: Built-in (HTTP Request node)
URL: http://minio:9000/minio/health/live
Method: GET
```

---

## 📝 Créer Custom Workflows

### Template: Pipeline Quotidienne

```javascript
// Node 1: Trigger
{
  "type": "cron",
  "cronExpression": "0 2 * * *"  // 2 AM daily
}

// Node 2: Execute Command
{
  "type": "n8n-nodes-base.executeCommand",
  "command": "cd /app && python run_pipeline.py --skip-download --use-minio --use-postgres"
}

// Node 3: Log to PostgreSQL
{
  "type": "n8n-nodes-base.postgres",
  "operation": "executeQuery",
  "query": `
    INSERT INTO pipeline_runs (run_date, status, records_processed)
    VALUES (NOW(), 'success', (SELECT COUNT(*) FROM weather_daily))
  `
}

// Node 4: Send Notification
{
  "type": "n8n-nodes-base.emailSend",
  "email": "admin@urbanhub.local",
  "subject": "UrbanHub Pipeline - {{ $now }}",
  "text": "Pipeline executed successfully"
}
```

### Template: Data Quality Check

```javascript
// Node 1: Trigger (hourly)
{
  "type": "cron",
  "cronExpression": "0 * * * *"  // Every hour
}

// Node 2: Query PostgreSQL
{
  "type": "n8n-nodes-base.postgres",
  "query": `
    SELECT 
      COUNT(*) as record_count,
      COUNT(CASE WHEN temperature_mean IS NULL THEN 1 END) as null_temps
    FROM weather_daily
    WHERE date = CURRENT_DATE
  `
}

// Node 3: IF Check
{
  "condition": "{{ $node['Query'].data.record_count < 1000 }}",
  "then": "SEND_ALERT",
  "else": "OK"
}

// Node 4: Send Alert
{
  "type": "n8n-nodes-base.emailSend",
  "email": "alert@urbanhub.local",
  "subject": "⚠️ Data Quality Alert"
}
```

### Template: Export to Cloud

```javascript
// Node 1: Trigger (weekly Sunday)
{
  "type": "cron",
  "cronExpression": "0 0 * * 0"  // Every Sunday
}

// Node 2: Export from PostgreSQL
{
  "type": "n8n-nodes-base.postgres",
  "operation": "executeQuery",
  "query": "SELECT * FROM weather_daily WHERE date >= NOW() - INTERVAL '7 days'"
}

// Node 3: Save to S3 (MinIO)
{
  "type": "n8n-nodes-base.aws",
  "operation": "putObject",
  "bucket": "urbanhub",
  "key": "exports/weekly_{{ $now }}.parquet"
}

// Node 4: Archive
{
  "type": "n8n-nodes-base.aws",
  "operation": "copyObject",
  "source": "urbanhub/exports/...",
  "destination": "urbanhub-archive/..."
}
```

---

## 🔄 Cron Expressions

```
# Every day at 2 AM
0 2 * * *

# Every 6 hours
0 */6 * * *

# Every Monday at 9 AM
0 9 * * 1

# Every 15 minutes
*/15 * * * *

# First day of month at 0 AM
0 0 1 * *

# Every Friday at 6 PM
0 18 * * 5
```

---

## 🚀 Trigger Types

### Cron (Scheduling)
```json
{
  "type": "n8n-nodes-base.cron",
  "cronExpression": "0 2 * * *"
}
```

### Webhook (External Triggers)
```json
{
  "type": "n8n-nodes-base.webhook",
  "method": "POST",
  "path": "/pipeline-trigger"
}
// Usage: POST http://n8n:5678/webhook/pipeline-trigger
```

### Manual (Button Click)
```json
{
  "type": "n8n-nodes-base.start"
}
// Exécution manuelle via UI
```

---

## 📊 Node Types Disponibles

### Data Query
- `postgres` - Query PostgreSQL
- `mysql` - Query MySQL
- `http` - HTTP Requests

### Execution
- `executeCommand` - Shell commands
- `executeWorkflow` - Chain workflows

### Storage
- `aws-s3` - MinIO uploads
- `google-cloud-storage` - GCS

### Notification
- `emailSend` - Email alerts
- `slack` - Slack messages
- `discord` - Discord webhook

### Conditional
- `if` - IF/ELSE logic
- `switch` - Multi-branch logic

---

## 🔍 Debugging

### Enable Logging

```
1. Settings → Logging
2. Set level: DEBUG
3. View logs: Executions → Recent
```

### Test Workflow

```
1. Click "Test workflow"
2. Select trigger type
3. View execution results
4. Check node outputs
```

### Node Output

```javascript
// Access previous node data
{{ $node['NodeName'].data.field }}
{{ $node['Query'].data[0].count }}
{{ $now }}        // Current time
{{ $env.VAR_NAME }} // Environment
```

---

## 📈 Monitoring

### Execution History

```
Menu → Executions
- View all past runs
- Check success/failure
- See execution time
- Debug with full logs
```

### Workflow Status

```
Dashboard:
- Active workflows
- Execution count
- Success rate
- Average duration
```

### Alerts Setup

```
Workflow → Settings → Error
- On failure: Send email
- On timeout: Retry logic
- Notifications: Slack/Discord
```

---

## 🔐 Security

### Credentials

Toutes les credentials sont **encryptées**:
- PostgreSQL passwords
- SSH keys
- API tokens
- S3 secrets

### Access Control

```
n8n Admin Panel:
- User management
- Role-based access
- Audit logs
- IP whitelisting
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Workflow won't start**
- Check trigger configuration
- Verify PostgreSQL connection
- Check n8n service running

**Command execution fails**
- Verify SSH credentials
- Check command syntax
- Review logs for errors

**PostgreSQL connection error**
- Verify host:port
- Check credentials
- Test with psql client

### Debug Mode

```bash
# Check n8n logs
docker-compose logs n8n

# Database status
docker-compose exec n8n npm run health

# Restart n8n
docker-compose restart n8n
```

---

## 📚 Resources

- [n8n Documentation](https://docs.n8n.io)
- [Workflows Examples](https://n8n.io/workflows)
- [Community Forum](https://community.n8n.io)

---

## 🎯 Next Steps

1. **Import** `urbanhub_daily_pipeline.json`
2. **Configure** PostgreSQL credentials
3. **Test** workflow execution
4. **Deploy** and monitor
5. **Create** custom workflows as needed

Happy automation! 🚀
