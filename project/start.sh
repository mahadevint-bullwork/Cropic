#!/bin/bash
# Start auto_assign in background
python3 auto_assign.py &

# Start server
node server.js