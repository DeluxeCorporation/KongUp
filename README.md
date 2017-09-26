# KongUp

## Intro 

KongUp automatically add APIs to Kong as soon as they're deployed to a
rancher/cattle machine.

## Labels 

Your services must have some docker labels on them in order for KongUp
to detect it.

GATEWAY_VISIBLE => Either True or False. Required.

GATEWAY\_URI => Kong uri (kong version>= 0.10.0) property. Required.

ENVIRONMENT => The envivronment of the gateway to which the api should
be added. Required. all caps


STRIP\_URI => When matching an API via one of the uris
prefixes, strip that matching prefix from the upstream URI to be
requested. Optionl. Defaults to 'True'. Value must be one of
'True', 'False', or ''.

## Environment Variables 


KONG\_UP\_KONG\_ENVIRONMENT => Which environment is this kong for?
Must be one of DEV, QA, UAT, XUAT, PREPROD, PROD. Required. All CAPS.

KONG\_UP\_KONG\_HOST => Hostname of machine where kong is
installed. Required.

KONG\_UP\_HIPCHAT\_URL => HipChat link to post to. Required.

KONG\_UP\_LOG\_LEVEL => One of DEBUG, INFO, WARN, ERROR, FATAL


## Running in Docker

``` docker run -d \ -v /run/docker.sock:/var/run/docker.sock \ -e
KONG_UP_KONG_ENVIRONMENT="DEV" \ -e
KONG_UP_KONG_HOST="dev.api.deluxe.com" \ -e
KONG_UP_HIPCHAT_URL="xxx.com"\ -e KONG_UP_LOG_LEVEL="DEBUG"\
kong_up_image_name ```

## Quick troubleshooting

Check the logs to see if there are any expections. There are no
external dependencies, so everything should work as expected.

## Supported Versions 

KongUp was tested on the following environment

- Rancher == 1.6.2
- Kong == 0.11.0
- Docker == 1.12.6

