clean:
	@rm -rf build
	@rm -rf dist
	@rm -rf docs/_build/*
	@rm -rf opts.egg-info
	@rm -f distribute-*
	@rm -f *.pyc

doc:
	@cd docs; make html

test:
	@python setup.py test
