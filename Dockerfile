FROM golang:1.11 as builder
ADD src /src
RUN go get -d ../src/deployer/ && go build -o deployer ../src/deployer/main.go && mv deployer ./bin/ && chmod +x ./bin/*

FROM python:3.6-jessie 
## Add signed certificate 
#RUN mkdir /usr/local/share/ca-certificates
#COPY you-certificate.crt /usr/local/share/ca-certificates

# Define rancher compose version
ENV RANCHER_CLI_VERSION v0.6.12

# Download and install rancher compose at specified version
RUN apt-get -yqq update && \
		apt-get install -yqq --no-install-recommends ca-certificates wget curl jq netcat && \
		apt-get -y install gettext-base && \
		wget -qO- https://github.com/rancher/cli/releases/download/${RANCHER_CLI_VERSION}/rancher-linux-amd64-${RANCHER_CLI_VERSION}.tar.gz | tar xvz -C /tmp && \
		mv /tmp/rancher-${RANCHER_CLI_VERSION}/rancher /usr/local/bin/rancher && \
		chmod +x /usr/local/bin/rancher

# Cleanup image
RUN apt-get -yqq autoremove && \
		apt-get -yqq clean && \
		rm -rf /var/lib/apt/lists/* /var/cache/* /tmp/* /var/tmp/*

# Update certificates list
RUN update-ca-certificates

# Define working directory.
WORKDIR /workspace

COPY --from=builder /go/bin/deployer /bin/deployer
COPY requirements.txt compose_update.py ./
RUN python -m pip install -r requirements.txt
# Some anchor endpoint
CMD tail -f /dev/null
