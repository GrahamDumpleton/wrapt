.PHONY : all

all :

install : all
	pip install -U .

package :
	python3.6 setup.py sdist bdist_wheel

release : clean package
	twine upload dist/*

clean :
	rm -rf build dist wrapt.egg-info

test :
	tox --skip-missing-interpreters
