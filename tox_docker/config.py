from typing import Collection, Dict, Mapping, Optional
import os.path

from docker.models.containers import Container as DockerContainer
from docker.types import Mount

RunningContainers = Dict[str, DockerContainer]


class Image:
    def __init__(self, config_line: str) -> None:
        self.name, _, tag = config_line.partition(":")
        self.tag = tag or None

    def __str__(self) -> str:
        if self.tag:
            return f"{self.name}:{self.tag}"
        return self.name

    def __repr__(self) -> str:
        return repr(str(self))


class Port:
    def __init__(self, config_line: str) -> None:
        host_port, _, container_port_proto = config_line.partition(":")
        container_port, _, protocol = container_port_proto.partition("/")

        if protocol.lower() not in ("tcp", "udp"):
            raise ValueError("protocol must be tcp or udp")
        if not host_port.isdigit():
            raise ValueError("host port must be an int")
        if not container_port.isdigit():
            raise ValueError("container port must be an int")

        self.host_port = int(host_port)
        self.container_port_proto = container_port_proto


class Link:
    def __init__(self, config_line: str) -> None:
        target, sep, alias = config_line.partition(":")

        if sep and not alias:
            raise ValueError(f"Link '{target}:' missing alias")

        self.target = target
        self.alias = alias or target


class Volume:
    def __init__(self, config_line: str) -> None:
        parts = config_line.split(":")
        if len(parts) != 4:
            raise ValueError(f"Volume {config_line!r} is malformed")
        if parts[0] != "bind":
            raise ValueError(f"Volume {config_line!r} type must be 'bind:'")
        if parts[1] not in ("ro", "rw"):
            raise ValueError(f"Volume {config_line!r} options must be 'ro' or 'rw'")

        volume_type, mode, outside, inside = parts
        if not os.path.isabs(outside):
            raise ValueError(f"Volume source {outside!r} must be an absolute path")
        if not os.path.isabs(inside):
            raise ValueError(f"Mount point {inside!r} must be an absolute path")

        self.docker_mount = Mount(
            source=outside,
            target=inside,
            type=volume_type,
            read_only=bool(mode == "ro"),
        )


class ContainerConfig:
    def __init__(
        self,
        name: str,
        image: Image,
        stop: bool,
        environment: Optional[Mapping[str, str]] = None,
        healthcheck_cmd: Optional[str] = None,
        healthcheck_interval: Optional[float] = None,
        healthcheck_timeout: Optional[float] = None,
        healthcheck_start_period: Optional[float] = None,
        healthcheck_retries: Optional[int] = None,
        ports: Optional[Collection[Port]] = None,
        links: Optional[Collection[Link]] = None,
        volumes: Optional[Collection[Volume]] = None,
    ) -> None:
        self.name = name
        self.image = image
        self.stop = stop
        self.environment: Mapping[str, str] = environment or {}
        self.ports: Collection[Port] = ports or {}
        self.links: Collection[Link] = links or {}
        self.mounts: Collection[Mount] = [v.docker_mount for v in volumes or ()]

        self.healthcheck_cmd = healthcheck_cmd
        self.healthcheck_interval = (
            int(healthcheck_interval) if healthcheck_interval else None
        )
        self.healthcheck_timeout = (
            int(healthcheck_timeout) if healthcheck_timeout else None
        )
        self.healthcheck_start_period = (
            int(healthcheck_start_period) if healthcheck_start_period else None
        )
        self.healthcheck_retries = healthcheck_retries
