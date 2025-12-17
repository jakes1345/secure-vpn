#!/bin/bash
# Update Nginx to serve SearXNG at /search

FILE="/etc/nginx/sites-available/phazevpn"

# Add location block if not present
if ! grep -q "location /search" "$FILE"; then
    sed -i '/location \/ {/i \    # SearXNG Search Engine\n    location /search/ {\n        proxy_pass http://localhost:8080/;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_set_header X-Script-Name /search;\n    }\n' "$FILE"
    
    echo "Updated Nginx configuration."
    nginx -t && systemctl reload nginx
    echo "Nginx reloaded."
else
    echo "Search location already exists."
fi
