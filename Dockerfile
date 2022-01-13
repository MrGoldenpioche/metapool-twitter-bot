#Create ubuntu as base image
FROM ubuntu
WORKDIR /twitter-bot

#Install packages
RUN ["apt-get", "update", "-y"]
RUN ["apt-get", "install","vim", "python3", "python3-pip",  "ca-certificates" ,"curl", "gnupg" ,"lsb-release", "git" ,"-y"]
RUN ["pip", "install", "pipenv"]
COPY ["Pipfile*","twitter-bot.py","/twitter-bot/"]
RUN ["pipenv", "install","--system", "--deploy","--ignore-pipfile" ]
CMD ["python3","-u", "twitter-bot.py" ]
