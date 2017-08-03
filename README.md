# KongUp

## Intro 

KongUp automatically add APIs to Kong as soon as they're reployed to a rancher/cattle machine.

## Labels 

Your services must have some docker labels on them in order for KongUp to detect it.

GATEWAY_VISIBLE => Either True or False. Required.

GATEWAY\_REQUEST\_PATH => request\_path (kong version <0.10.0) or uri (kong version>= 0.10.0) property. Required.

ENVIRONMENT => The envivronment of the gateway to which the api should be added. Required.

## Environment Variables 

HOSTNAME => This is usually set by your operating system. Just ensure 
that it is set

DEV\_KONG\_HOST => Hostname of machine where DEV kong is running. Required.

QA\_KONG\_HOST => Hostname of machine where QA kong is running. Required.

UAT\_KONG\_HOST => Hostname of machine where UAT kong is running. Required.

XUAT\_KONG\_HOST => Hostname of machine where XUAT kong is running. Required.

PREPROD\_KONG\_HOST => Hostname of machine where PREPROD kong is running. Required.

PROD\_KONG\_HOST => Hostname of machine where PROD kong is running. Optional.

## Running in Docker

```
docker run -d -v /run/docker.sock:/var/run/docker.sock -v /usr/sbin/iptables:/usr/sbin/iptables -v /run/docker.sock:/var/run/docker.sock --network "host" --privileged --pid "host" -e  DEV_KONG_HOST="dev.api.deluxe.com" -e  QA_KONG_HOST="qa.api.deluxe.com" -e  UAT_KONG_HOST="xuat.api.deluxe.com" -e  XUAT_KONG_HOST="xuat.api.deluxe.com" -e  PREPROD_KONG_HOST="preprod.api.deluxe.com" -e  PROD_KONG_HOST="prod.api.deluxe.com" kong_up_image_name
```

## Quicktrouble shooting

Check the logs to see if there are any expections. There are no external dependencies, so everything should work as expected.

## Supported Rancher versions

- >= 1.6.0
