from typing import List, Any, Union, Optional

import inspect
from dataclasses import dataclass, make_dataclass, field

from omegaconf import MISSING
from hydra.core.config_store import ConfigStore

import torch_geometric


def to_dataclass(cls: Any) -> Any:
    r"""Converts a given class :obj:`cls` to a `dataclass` schema."""
    fields = []
    for name, parameter in inspect.signature(cls.__init__).parameters.items():
        if name in {'self', 'args', 'kwargs'}:
            continue

        item = (name, )

        annotation = parameter.annotation
        if annotation != inspect.Parameter.empty:
            # `Union` types are not supported (except `Optional`).
            # As such, we replace them with either `Any` or `Optional[Any]`.
            origin = annotation.__dict__.get('__origin__', None)
            args = annotation.__dict__.get('__args__', None)
            if origin == Union and type(None) not in args:
                annotation = Any
            elif origin == Union and type(None) in args and len(args) > 2:
                annotation = Optional[Any]

            item = item + (annotation, )
        else:
            item = item + (Any, )

        default = parameter.default
        if default != inspect.Parameter.empty:
            if isinstance(default, (list, dict)):
                item = item + (field(default_factory=lambda: default), )
            else:
                item = item + (default, )
        else:
            item = item + (field(default=MISSING), )

        fields.append(item)

    full_cls_name = f'{cls.__module__}.{cls.__qualname__}'
    fields.append(('_target_', str, field(default=full_cls_name)))

    return make_dataclass(cls.__qualname__, fields=fields)


def register(group: str, package: Any, exclude: List[str] = []):
    for name in set(package.__all__) - set(exclude):
        Config = to_dataclass(getattr(package, name))
        config_store.store(group=group, name=name, node=Config)


config_store = ConfigStore.instance()


@dataclass
class Config:
    dataset: Any = MISSING


config_store.store(name='config', node=Config)

# Register `torch_geometric.transforms.*`:
register(group='transform', package=torch_geometric.transforms,
         exclude=['BaseTransform', 'AddMetaPaths'])

Config = to_dataclass(getattr(torch_geometric.datasets, 'Planetoid'))
config_store.store(group='dataset', name='Planetoid', node=Config)

# Register `torch_geometric.transforms.*`:
# register(group='dataset', package=torch_geometric.datasets)
