docgen= pdflatex
docgenopts= 
graphgen= dot
dotsource= $(wildcard *.dot)
images= $(patsubst %.dot, %.png,$(dotsource))

targets=$(images) odin_calibration.pdf

all : $(targets)

clean:
	rm -f $(targets) odin_calibration.aux odin_calibration.log odin_calibration.toc


%.pdf : %.tex
	$(docgen) $(docgenopts) $< -o $@
	$(docgen) $(docgenopts) $< -o $@

%.png : %.dot
	$(graphgen) -Tpng $< -o $@
