#!/usr/bin/make

SRC = firmware-flash.py

all:
	nuitka $(SRC) \
		--recurse-all \
		--show-scons \
		--python-version=3.6
