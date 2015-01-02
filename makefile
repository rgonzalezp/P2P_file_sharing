# makefile


.PHONY: default
default: clean


# run the server
.PHONY: s
s:
	python server.py


# run client user_0001
.PHONY: 1
1:
	python client.py user_0001


# run client user_0002
.PHONY: 2
2:
	python client.py user_0002


# run client user_0003
.PHONY: 3
3:
	python client.py user_0003


# remove Python bytecode and JSON files
clean:
	find . -type f -name "*.pyc" -exec rm -vf {} \;
	find . -type f -name "*.json" -exec rm -vf {} \;
