# makefile

# Dimitrios Paraschas
# 1562
# Dimitrios Greasidis
# 1624
# Stefanos Papanastasiou
# 1608


.PHONY: default
default: clean


# reset the server
reset_server:
	rm -f server/configuration.json
	rm -f server/clients.json
	rm -f server/server.log

# reset the client
reset_client:
	rm -f client/configuration.json
	rm -f client/client.log


# remove Python bytecode, JSON, and log files
clean:
	find . -type f -name "*.pyc" -exec rm -vf {} \;
	find . -type f -name "*.json" -exec rm -vf {} \;
	find . -type f -name "*.log" -exec rm -vf {} \;
