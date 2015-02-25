FROM python:2-onbuild
MAINTAINER Stefan Verhoeven "s.verhoeven@esciencecenter.nl"
EXPOSE 6566
RUN python setup.py develop
CMD pserve docker.ini
