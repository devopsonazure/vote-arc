FROM tiangolo/uwsgi-nginx-flask:python3.9
RUN pip install redis
ADD /azure-vote /app
