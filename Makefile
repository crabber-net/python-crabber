requirements:
	poetry export --without-hashes -f requirements.txt > requirements.txt

test:
	poetry run pytest --cov=crabber/ tests/
