# Banking System Monitoring Guide

## Overview
Your distributed banking system now includes comprehensive monitoring with Prometheus and Grafana. This provides real-time insights into system performance, business metrics, and operational health.

## Services

### Prometheus (Port 9090)
- **URL**: http://localhost:9090
- **Purpose**: Metrics collection and storage
- **Scrape Interval**: 15 seconds

### Grafana (Port 3000)
- **URL**: http://localhost:3000
- **Default Credentials**:
  - Username: `admin`
  - Password: `admin`
- **Purpose**: Visualization and dashboards

## Getting Started

### 1. Start Monitoring Services
```bash
docker compose up -d
```

This starts all services including Prometheus and Grafana.

### 2. Access Grafana
1. Open http://localhost:3000 in your browser
2. Login with `admin` / `admin`
3. You'll be prompted to change the password (recommended)
4. Navigate to "Dashboards" → "Banking System Overview"

### 3. Access Prometheus
1. Open http://localhost:9090
2. Use the "Graph" tab to query metrics directly
3. Check "Status" → "Targets" to verify the backend is being scraped

## Available Metrics

### HTTP/API Metrics
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- Response time percentiles (p50, p95, p99)

### Business Metrics
- `banking_transactions_total` - Total transactions (completed/failed)
- `banking_transaction_amount` - Transaction amount distribution
- `banking_accounts_total` - Active accounts count
- `banking_users_total` - Registered users count

### Database Metrics
- `db_queries_total` - Database queries by operation type
- `db_query_duration_seconds` - Query execution time
- `db_connections_active` - Active database connections

### Cache Metrics
- `cache_operations_total` - Cache operations (get/set/delete)
- `cache_hit_ratio` - Cache effectiveness (0-1)
- Hit/miss rates by operation

### Kafka Metrics
- `kafka_messages_produced_total` - Messages sent to Kafka by topic
- `kafka_producer_errors_total` - Producer error count

### Authentication Metrics
- `auth_attempts_total` - Login attempts (success/failure)
- `auth_active_sessions` - Current active sessions

### Error Metrics
- `errors_total` - Application errors by type and endpoint

## Dashboard Guide

### Banking System Overview Dashboard

The pre-configured dashboard includes:

1. **Request Rate** - Real-time API request throughput
   - Shows requests per second by endpoint
   - Useful for identifying traffic patterns

2. **95th Percentile Response Time** - Gauge showing API performance
   - Green: < 0.5s (good)
   - Yellow: 0.5-1s (warning)
   - Red: > 1s (critical)

3. **Transaction Rate by Status** - Business health
   - Completed vs failed transactions
   - Helps identify transaction issues

4. **Total Active Accounts** - Business metric
   - Current number of active accounts

5. **Total Users** - User base size

6. **Cache Hit Ratio** - Cache effectiveness
   - Green: > 80% (efficient)
   - Yellow: 50-80% (acceptable)
   - Red: < 50% (needs attention)

7. **Active DB Connections** - Database load
   - Monitor connection pool usage

8. **Average Database Query Duration** - DB performance
   - Track slow queries by operation type

9. **Error Rate** - System reliability
   - Errors per second by type

## Common Prometheus Queries

### Request Rate
```promql
rate(http_requests_total[5m])
```

### Error Rate
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### 95th Percentile Response Time
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Successful Transaction Rate
```promql
rate(banking_transactions_total{status="completed"}[5m])
```

### Cache Hit Ratio
```promql
cache_hit_ratio
```

### Database Query Rate by Operation
```promql
rate(db_queries_total[5m])
```

## Setting Up Alerts

### 1. In Grafana
1. Navigate to "Alerting" → "Alert rules"
2. Click "New alert rule"
3. Configure conditions (e.g., error rate > 10/min)
4. Set up notification channels (email, Slack, etc.)

### 2. Example Alert: High Error Rate
```yaml
alert: HighErrorRate
expr: rate(errors_total[5m]) > 0.1
for: 5m
labels:
  severity: critical
annotations:
  summary: High error rate detected
  description: Error rate is {{ $value }} errors/sec
```

### 3. Example Alert: Low Cache Hit Ratio
```yaml
alert: LowCacheHitRatio
expr: cache_hit_ratio < 0.5
for: 10m
labels:
  severity: warning
annotations:
  summary: Cache hit ratio is low
  description: Current hit ratio is {{ $value }}
```

## Custom Dashboards

### Creating Your Own Dashboard

1. In Grafana, click "+" → "Dashboard"
2. Click "Add new panel"
3. Enter a Prometheus query
4. Configure visualization type (Graph, Gauge, Stat, etc.)
5. Set thresholds and units
6. Save the dashboard

### Example Panel: Failed Transactions
```promql
Query: sum(rate(banking_transactions_total{status="failed"}[5m]))
Visualization: Graph
Unit: ops/sec
Threshold: Warning at 5, Critical at 10
```

## Monitoring Best Practices

### 1. Regular Checks
- Review dashboards daily
- Check for anomalies in traffic patterns
- Monitor error rates and response times

### 2. Set Up Alerts
- Configure alerts for critical metrics
- Use escalation policies
- Test alerts regularly

### 3. Capacity Planning
- Monitor resource usage trends
- Track growth in users and transactions
- Plan scaling based on metrics

### 4. Performance Optimization
- Identify slow endpoints using p95/p99 latency
- Optimize queries with high duration
- Improve cache hit ratio by adjusting TTL

### 5. Business Insights
- Track transaction volumes and patterns
- Monitor user growth
- Analyze peak usage times

## Troubleshooting

### Prometheus Not Scraping Backend
1. Check backend is running: `docker compose ps`
2. Verify metrics endpoint: `curl http://localhost:8000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Review Prometheus logs: `docker compose logs prometheus`

### Grafana Can't Connect to Prometheus
1. Verify Prometheus is running: `docker compose ps prometheus`
2. Check datasource configuration in Grafana
3. Test connection in "Configuration" → "Data Sources"

### Missing Metrics
1. Ensure the backend code is instrumented
2. Trigger some API calls to generate metrics
3. Refresh Grafana dashboard
4. Check metric names in Prometheus: http://localhost:9090/graph

### High Memory Usage
1. Adjust Prometheus retention: `--storage.tsdb.retention.time=15d`
2. Reduce scrape interval in prometheus.yml
3. Limit metric cardinality (avoid high-cardinality labels)

## API Endpoints

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```
Returns Prometheus-formatted metrics from the backend.

### Health Check
```bash
curl http://localhost:8000/health
```
Returns system health status.

## Extending Monitoring

### Add Custom Metrics
Edit `backend/monitoring/metrics.py`:

```python
from prometheus_client import Counter

custom_metric = Counter(
    'custom_metric_name',
    'Description',
    ['label1', 'label2']
)

# Use in code
custom_metric.labels(label1='value1', label2='value2').inc()
```

### Add Redis Exporter (Optional)
```yaml
redis-exporter:
  image: oliver006/redis_exporter:latest
  ports:
    - "9121:9121"
  environment:
    REDIS_ADDR: redis:6379
```

### Add PostgreSQL Exporter (Optional)
```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter:latest
  ports:
    - "9187:9187"
  environment:
    DATA_SOURCE_NAME: "postgresql://postgres:password@postgres:5432/bankingdb?sslmode=disable"
```

## Retention and Storage

### Prometheus Data Retention
Default: 15 days

To change:
```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'
```

### Grafana Backup
```bash
# Backup Grafana data
docker compose cp grafana:/var/lib/grafana ./grafana-backup

# Restore
docker compose cp ./grafana-backup/. grafana:/var/lib/grafana
```

## Security Considerations

1. **Change Default Passwords**
   - Grafana admin password
   - Consider adding authentication to Prometheus

2. **Network Security**
   - Restrict monitoring ports in production
   - Use reverse proxy with authentication

3. **Data Retention**
   - Review retention policies
   - Implement data backup strategies

## Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **PromQL Tutorial**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Dashboards**: https://grafana.com/grafana/dashboards/

## Support

For issues or questions:
1. Check logs: `docker compose logs [service]`
2. Review metrics: http://localhost:9090
3. Inspect targets: http://localhost:9090/targets
4. Test API: `curl http://localhost:8000/metrics`
