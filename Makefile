all:
	echo do nothing.

clean:
	echo -n > logs/django.log
	rm -f db.sqlite3
	rm -rf file_upload/__pycache__/ file_upload/migrations/__pycache__/ file_upload/templatetags/__pycache__/ upload/__pycache__/
	rm -f file_upload/migrations/*_initial.py

