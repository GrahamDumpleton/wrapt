.PHONY : all

all :

install : all
	pip install -U .

package :
	python setup.py sdist

release :
	@echo "ERROR: Direct releases are no longer supported from this Makefile."
	@echo "Release packages are built by GitHub Actions."
	@echo "Push a tag to trigger the build workflow."
	@exit 1

mostlyclean :
	rm -rf .coverage.*

clean : mostlyclean
	rm -rf build dist src/wrapt.egg-info .tox

test :
	tox --skip-missing-interpreters
