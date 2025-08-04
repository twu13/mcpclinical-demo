.PHONY: data server ngrok stop all client dev 

# Generate synthetic data
data:
	python support/generate_clinical.py

# Run clinical_mcp.py server
server:
	@echo "Starting clinical MCP server on port 8000..."
	python clinical_mcp.py

# Run ngrok to expose the server
ngrok:
	ngrok http 8000 & \
	sleep 5; \
	export URL=$$(curl -s http://localhost:4040/api/tunnels | grep -Eo 'https://[a-zA-Z0-9\-]+\.ngrok-free\.app' | head -n 1); \
	echo "{\"server_url\": \"$$URL/sse\"}" > config.json;

# Stop any running servers
stop:
	@echo "Stopping any running servers..."
	@-pkill -f clinical_mcp.py 2>/dev/null || true
	@-pkill -f ngrok 2>/dev/null || true
	@echo "Servers stopped"

# Run both data generation and server
all: data server

# Run client.py
client:
	streamlit run clinical_dashboard.py

# Run everything: data, server, ngrok, then client (client is foreground)
dev:
	@trap "pkill -P $$; exit" INT TERM
	@$(MAKE) data
	@$(MAKE) server > /dev/null 2>&1 &
	@sleep 2
	@ngrok http 8000 > /dev/null 2>&1 & \
	sleep 5; \
	export URL=$$(curl -s http://localhost:4040/api/tunnels | grep -Eo 'https://[a-zA-Z0-9\-]+\.ngrok-free\.app' | head -n 1); \
	echo "{\"server_url\": \"$$URL/sse\"}" > config.json;
	@sleep 1
	streamlit run clinical_dashboard.py
