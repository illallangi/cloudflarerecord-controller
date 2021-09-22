from .configmap import rpz_config_map
import kopf

CRD_GROUP = "controllers.illallangi.enterprises"
CRD_VERSION = "v1"
CRD_SINGULAR = "cloudflarerecord"


@kopf.index(
    group=CRD_GROUP,
    version=CRD_VERSION,
    singular=CRD_SINGULAR,
)
async def dns_resource_record_idx(
    namespace,
    body,
    **_,
):
    return {
        namespace: {k: body[k] for k in body},
    }


@kopf.on.probe(
    id=dns_resource_record_idx.__name__,
)
async def dns_resource_record_probe(
    dns_resource_record_idx: kopf.Index,
    **_,
):
    return {
        namespace: [o for o in dns_resource_record_idx[namespace]]
        for namespace in dns_resource_record_idx
    }


@kopf.on.event(
    group=CRD_GROUP,
    version=CRD_VERSION,
    singular=CRD_SINGULAR,
)
async def dns_resource_record_event(**kwargs):
    await rpz_config_map(**kwargs)
