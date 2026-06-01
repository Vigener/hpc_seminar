.PHONY: all run clean

build: matvec_original matvec_loopswap matvec_padding matvec_loopswap_padding


matvec_original: matvec_original.c
	mkdir -p bin
	gcc -O3 matvec_original.c -o bin/matvec_original -lm

matvec_loopswap: matvec_loopswap.c
	mkdir -p bin
	gcc -O3 matvec_loopswap.c -o bin/matvec_loopswap -lm

matvec_padding: matvec_padding.c
	mkdir -p bin
	gcc -O3 matvec_padding.c -o bin/matvec_padding -lm

matvec_loopswap_padding: matvec_loopswap_padding.c
	mkdir -p bin
	gcc -O3 matvec_loopswap_padding.c -o bin/matvec_loopswap_padding -lm

clean:
	rm -f bin/matvec_original bin/matvec_loopswap