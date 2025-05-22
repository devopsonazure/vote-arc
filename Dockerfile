FROM tiangolo/uwsgi-nginx-flask:python3.6
RUN pip install redis Flask-WTF
ADD /azure-vote /app
