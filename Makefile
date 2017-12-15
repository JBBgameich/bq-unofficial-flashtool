#!/usr/bin/make

SRC = firmware-flash.py
BIN = firmware-flash.exe
OBJ = firmware-flash.build

all:
	nuitka $(SRC) \
		--recurse-all \
		--show-scons \
		--unstripped \
		--python-version=3.6

clean:
	rm $(BIN) $(OBJ) -r
