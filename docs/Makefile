# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@if [ -d sphinxvenv ]; then echo "Using Sphinx Python virtual environment in `pwd`/sphinxvenv"; fi;
	@[ -d sphinxvenv ] && source sphinxvenv/bin/activate; $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

apidoc:
	@if [ -d sphinxvenv ]; then echo "Using Sphinx Python virtual environment in `pwd`/sphinxvenv"; fi;
	@[ -d sphinxvenv ] && source sphinxvenv/bin/activate; sphinx-apidoc -f -M -T -e -o source ../pdg

sphinxvenv:
	@echo 'Creating Sphinx Python virtual environment that will be used for building docs in the future'
	@virtualenv -p python3 sphinxvenv
	@source sphinxvenv/bin/activate; pip install --upgrade pip
	@source sphinxvenv/bin/activate; pip install -r sphinx-requirements.txt

version:
	@[ -d sphinxvenv ] && source sphinxvenv/bin/activate; python --version
