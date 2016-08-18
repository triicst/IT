FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y -qq
RUN apt-get install -y -qq libunwind8 libicu55 wget
RUN wget -q https://github.com/PowerShell/PowerShell/releases/download/v6.0.0-alpha.9/powershell_6.0.0-alpha.9-1ubuntu1.16.04.1_amd64.deb
RUN dpkg -i powershell_6.0.0-alpha.9-1ubuntu1.16.04.1_amd64.deb

ENTRYPOINT ["/usr/bin/powershell"]
