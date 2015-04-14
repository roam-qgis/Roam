all: clean build test

test:
	py.test tests

build: clean
	python setup.py build

clean:
	python setup.py clean

package: clean build
	python setup.py py2exe

run:
	python src/roam
