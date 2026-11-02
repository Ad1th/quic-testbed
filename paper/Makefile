# make        -> regenerate numbers/tables/figures from data/rigor and build main.pdf
# Needs: pandas, numpy, scipy, matplotlib (PY), pdflatex + bibtex.
PY ?= python3
main.pdf: main.tex refs.bib gen/numbers.tex
	pdflatex -interaction=nonstopmode main.tex >/dev/null
	bibtex main >/dev/null
	pdflatex -interaction=nonstopmode main.tex >/dev/null
	pdflatex -interaction=nonstopmode main.tex | grep -E "^!|Output written"
gen/numbers.tex: make_assets.py $(wildcard ../data/rigor/*.csv)
	cd .. && $(PY) paper/make_assets.py >/dev/null
clean:
	rm -f *.aux *.bbl *.blg *.log *.out build.log
.PHONY: clean
