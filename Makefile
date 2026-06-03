
NAME = wraith
CFLAGS = -O2 -s

compile:
	gcc $(CFLAGS) $(NAME).c -o $(NAME) 

clean:
	rm wraith