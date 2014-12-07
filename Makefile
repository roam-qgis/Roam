all: clean build test
test:
	py.test tests

build: clean
	python setup.py build

clean:
	python setup.py clean

