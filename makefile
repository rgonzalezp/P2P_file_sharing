# makefile


.PHONY: default
default: clean


# run the server
.PHONY: s
s:
	python server.py


# run client 1
.PHONY: 1
1:
	python client.py 1


# run client 2
.PHONY: 2
2:
	python client.py 2


# run client 3
.PHONY: 3
3:
	python client.py 3


# remove Python bytecode and JSON files
clean:
	find . -type f -name "*.pyc" -exec rm -vf {} \;
	find . -type f -name "*.json" -exec rm -vf {} \;
