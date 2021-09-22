import os
import kubernetes
import kopf
import pathlib
from kubernetes.client.rest import ApiException
from .labels import Labels
from yaml import load, Loader
from jinja2 import Environment, FileSystemLoader, select_autoescape
from os.path import join
import time
from more_itertools import one

LABEL_COMPONENT = "app.kubernetes.io/component"
LABEL_CONTROLLER = "app.kubernetes.io/controller"
LABEL_INSTANCE = "app.kubernetes.io/instance"
LABEL_NAME = "app.kubernetes.io/name"

env = Environment(
    loader=FileSystemLoader(pathlib.Path(__file__).parent.absolute()),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.filters["path_join"] = lambda paths: join(*paths)
env.filters["match_object_by_labels"] = lambda objs, labels: one(
    [
        obj
        for obj in objs
        if all(
            [
                obj.get("metadata", {}).get("labels", {}).get(label, None)
                == labels[label]
                for label in labels
            ]
        )
    ]
)

env.filters["match_instance_label"] = lambda objs, instance: [
    obj
    for obj in objs
    if obj.get("metadata", {}).get("labels", {}).get(LABEL_INSTANCE, None)
    == instance
]


@kopf.index(
    "configmap",
    labels={
        LABEL_NAME: "cloudflarerecord",
        LABEL_COMPONENT: "ddns",
    },
)
async def rpz_config_map_idx(namespace, body, **_):
    return {
        namespace: {k: body[k] for k in body},
    }


@kopf.on.probe(id=rpz_config_map_idx.__name__)
async def rpz_config_map_probe(rpz_config_map_idx: kopf.Index, **_):
    return {
        namespace: [o for o in rpz_config_map_idx[namespace]]
        for namespace in rpz_config_map_idx
    }


async def rpz_config_map(**kwargs):
    try:
        del kwargs["namespace"]
    except KeyError:
        pass

    api = kubernetes.client.CoreV1Api()
    namespace = os.environ.get("NAMESPACE")
    if namespace is None:
        raise kopf.PermanentError("NAMESPACE not defined")
    
    token = os.environ.get("TOKEN")
    if token is None:
        raise kopf.PermanentError("TOKEN not defined")

    # Define the object labels
    labels = Labels(
        **{
            LABEL_NAME: "cloudflarerecord",
            LABEL_COMPONENT: "ddns",
        }
    )

    # Define the object
    body = load(
        env.get_template("configmap.yaml.j2").render(
            namespace=namespace,
            token=token,
            serial=str(int(time.time())),
            **kwargs,
        ),
        Loader=Loader,
    )

    kopf.adjust_namespace(body, namespace)
    kopf.label(
        body,
        labels,
    )
    kopf.harmonize_naming(
        body,
        labels.asname,
        forced=True,
        strict=True,
    )

    # Patch existing object
    obj = None
    try:
        obj = api.patch_namespaced_config_map(
            namespace=namespace,
            name=body["metadata"]["name"],
            body=body,
        )
    except ApiException as ex:
        if ex.status != 404:
            raise

    # Create new object
    if obj is None:
        try:
            obj = api.create_namespaced_config_map(
                namespace=namespace,
                body=body,
            )
        except ApiException as ex:
            if ex.status != 409:
                raise
            # raise temporary error
            raise kopf.TemporaryError(
                "HTTP 409 Conflict; retrying in 15 seconds.", delay=15
            )
