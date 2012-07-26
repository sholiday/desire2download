clean:
	rm -Rf dist Desire2Download.egg-info

post: clean
	python setup.py sdist upload