# makefile


# remove Python bytecode, JSON, and log files
clean:
	find . -type f -name "*.pyc" -exec rm -vf {} \;
	find . -type f -name "*.json" -exec rm -vf {} \;
	find . -type f -name "*.log" -exec rm -vf {} \;
