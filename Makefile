.PHONY : all

all :

install : all
	pip install -U .

package :
	python setup.py sdist

release : clean package
	twine upload dist/*

mostlyclean:
	rm -rf .coverage.*

clean: mostlyclean
	rm -rf build dist src/wrapt.egg-info .tox

test :
	tox --skip-missing-interpreters
