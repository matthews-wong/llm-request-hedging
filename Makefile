.PHONY: test simulate validate

test:
	python3 -m unittest -q

simulate:
	python3 scripts/simulate.py

validate: test simulate
