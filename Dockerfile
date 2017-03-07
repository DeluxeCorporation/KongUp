FROM python:3-onbuild
RUN apt-get -y update
RUN apt-get -y install iptables
CMD [ "./entrypoint.sh" ]
