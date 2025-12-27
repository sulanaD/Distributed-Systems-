#!/bin/bash

echo "🧪 Testing Kafka Event Flow"
echo "=============================="
echo ""

# Login test user
echo "1. Logging in test user..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"kafka.test@example.com","password":"Test1234!"}' \
  | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ User logged in, got token"
echo ""

# Create two accounts
echo "2. Creating accounts..."
ACCOUNT1=$(curl -s -X POST http://localhost:8000/api/accounts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"account_type":"savings","initial_balance":1000}' \
  | jq -r '.account_number')

ACCOUNT2=$(curl -s -X POST http://localhost:8000/api/accounts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"account_type":"checking","initial_balance":500}' \
  | jq -r '.account_number')

echo "✅ Account 1: $ACCOUNT1"
echo "✅ Account 2: $ACCOUNT2"
echo ""

# Create a transfer (this will trigger Kafka events)
echo "3. Creating transfer (this triggers Kafka events)..."
TRANSFER=$(curl -s -X POST http://localhost:8000/api/transfers/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"from_account_number\":\"$ACCOUNT1\",\"to_account_number\":\"$ACCOUNT2\",\"amount\":100,\"description\":\"Kafka test transfer\"}" \
  | jq -r '.transaction_id')

echo "✅ Transfer created: $TRANSFER"
echo ""

echo "4. Waiting for consumers to process events..."
sleep 3
echo ""

echo "5. Checking consumer logs..."
echo ""
echo "📝 AUDIT CONSUMER (last 5 lines):"
docker compose logs audit-consumer --tail=5 | grep -E "(Audited|✓)"
echo ""

echo "📧 NOTIFICATION CONSUMER (last 5 lines):"
docker compose logs notification-consumer --tail=5 | grep -E "(EMAIL|To:|Message:)"
echo ""

echo "📊 ANALYTICS CONSUMER (last 5 lines):"
docker compose logs analytics-consumer --tail=5 | grep -E "(Processing|Milestone|Volume)"
echo ""

echo "✅ Test complete! Check the logs above for Kafka event processing."
