# KongUp

## Intro 

KongUp automatically add APIs to Kong as soon as they're reployed to a rancher/cattle machine.

## Labels 

Your services must have some docker labels on them in order for KongUp to detect it.

GATEWAY_VISIBLE => Either True or False. Required.

GATEWAY\_REQUEST\_PATH => request\_path (kong version <0.10.0) or uri (kong version>= 0.10.0) property. Required.

ENVIRONMENT => The envivronment of the gateway to which the api should be added. Required. all caps

## Environment Variables 

HOSTNAME => This is usually set by your operating system. Just ensure 
that it is set

KONG\_ENVIRONMENT => Environment of Kong host. Required. All Caps

KONG\_HOST => Hostname of machine where. Required.

HIPCHAT\_URL => HipChat link to post to. Required.

## Running in Docker

```
docker run -d \
-v /run/docker.sock:/var/run/docker.sock \
-v /usr/sbin/iptables:/usr/sbin/iptables \
-v /run/docker.sock:/var/run/docker.sock \
--network "host" \
--privileged \
--pid "host" \
-e KONG_ENVIRONMENT="DEV" \
-e KONG_HOST="dev.api.deluxe.com" \
-e HIPCHAT_URL="xxx.com"\
kong_up_image_name
```

## Quicktrouble shooting

Check the logs to see if there are any expections. There are no external dependencies, so everything should work as expected.

## Supported Rancher versions

- >= 1.6.0
