FROM python:3-onbuild
RUN apt-get -y update
RUN apt-get -y install nmap
CMD [ "./entrypoint.sh" ]
