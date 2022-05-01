run:
	poetry run python main_ui.py

build-exe:
	poetry run python setup.py build

build-installer:
	poetry run python setup.py bdist_msi