#!/bin/bash
# Benchmark PhazeVPN performance
# Run this on both server and client

set -e

echo "=========================================="
echo "📊 PhazeVPN Performance Benchmark"
echo "=========================================="
echo ""

# Check if running on server or client
if [ "$1" == "server" ]; then
    echo "🔧 Server Mode - Starting iperf3 server..."
    iperf3 -s -p 5201
    exit 0
fi

if [ -z "$1" ]; then
    echo "Usage:"
    echo "  Server: $0 server"
    echo "  Client: $0 <server-ip>"
    exit 1
fi

SERVER_IP=$1

echo "📊 Running benchmarks against $SERVER_IP"
echo ""

# Test 1: Latency
echo "1️⃣  Latency Test (ping):"
ping -c 10 $SERVER_IP | tail -2
echo ""

# Test 2: Throughput (TCP)
echo "2️⃣  Throughput Test (TCP):"
echo "   Running 60-second test..."
iperf3 -c $SERVER_IP -p 5201 -t 60 -f m | grep -E "(sender|receiver|Mbits/sec)"
echo ""

# Test 3: Throughput (UDP)
echo "3️⃣  Throughput Test (UDP):"
echo "   Running 60-second test..."
iperf3 -c $SERVER_IP -p 5201 -t 60 -u -b 1000M -f m | grep -E "(sender|receiver|Mbits/sec|lost)"
echo ""

# Test 4: Jitter
echo "4️⃣  Jitter Test:"
ping -c 100 -i 0.1 $SERVER_IP | grep -E "(min/avg/max|jitter)"
echo ""

# Test 5: Packet Loss
echo "5️⃣  Packet Loss Test:"
ping -c 1000 -i 0.01 $SERVER_IP | tail -1
echo ""

echo "=========================================="
echo "✅ Benchmark Complete!"
echo "=========================================="

