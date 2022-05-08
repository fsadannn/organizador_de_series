run:
	python main_ui.py

run-new:
	poetry run python new_main_ui.py

build-exe:
	poetry run python setup.py build

build-installer:
	poetry run python setup.py bdist_msi