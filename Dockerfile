FROM nestedtech/docker-python

RUN mkdir /app
WORKDIR /app

ADD ./ /app

RUN /root/virtualenv/bin/pip install -r requirements.txt --upgrade

ENV PYTHONPATH .

CMD ["/root/virtualenv/bin/python3", "-m", "looker_prometheus_exporter"]
