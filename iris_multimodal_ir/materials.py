"""Target-neutral typed material graphs and color semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one, optional
from .common import deep_freeze, identifiers, require_enum
from .enums import RequirementLevel
from .errors import IRAdmissionError, IRIntegrityError, IRSchemaError
from .identity import ExternalIdentityRef, IRNodeRef
from .resources import TextureResourceIR
from .versions import content_digest, require_finite_number, require_identifier, require_version

__all__ = [
    "MaterialPortIR", "MaterialNodeIR", "MaterialConnectionIR", "MaterialTerminalIR", "MaterialGraphIR",
    "MaterialIR", "MaterialBindingIR", "ColorValueIR", "ColorPipelineRef", "ColorConversionReceipt",
]


@dataclass(frozen=True, order=True)
class MaterialPortIR(IRRecord):
    port_id: str
    direction: str
    value_type: str
    requirement: RequirementLevel = RequirementLevel.REQUIRED

    def __post_init__(self) -> None:
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        object.__setattr__(self, "direction", require_identifier(self.direction, "direction"))
        if self.direction not in {"input", "output"}:
            raise IRSchemaError("material port direction must be input or output")
        object.__setattr__(self, "value_type", require_identifier(self.value_type, "value_type"))
        object.__setattr__(self, "requirement", require_enum(self.requirement, RequirementLevel, "requirement"))


@dataclass(frozen=True)
class MaterialNodeIR(IRRecord):
    node_id: str
    operation_family: str
    version: str
    ports: tuple[MaterialPortIR, ...]
    parameters: Mapping[str, Any] | None = None
    texture_refs: tuple[TextureResourceIR, ...] = ()
    trace_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"ports": many(MaterialPortIR), "texture_refs": many(TextureResourceIR), "trace_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "operation_family", require_identifier(self.operation_family, "operation_family"))
        object.__setattr__(self, "version", require_version(self.version))
        ports = tuple(MaterialPortIR.coerce(item, "ports[]") for item in self.ports)
        if len({item.port_id for item in ports}) != len(ports):
            raise IRSchemaError("material port ids must be unique within a node")
        object.__setattr__(self, "ports", tuple(sorted(ports, key=lambda item: item.port_id)))
        if self.parameters is not None:
            _validate_material_parameters(self.parameters, "parameters")
            object.__setattr__(self, "parameters", deep_freeze(self.parameters, "parameters"))
        object.__setattr__(self, "texture_refs", tuple(TextureResourceIR.coerce(item, "texture_refs[]") for item in self.texture_refs))
        refs = tuple(SemanticRef.coerce(item, "trace_refs[]") for item in self.trace_refs)
        object.__setattr__(self, "trace_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))


def _validate_material_parameters(value: Any, path: str) -> None:
    forbidden_keys = {"shader_source", "source_code", "executable", "workflow", "provider", "runtime", "script", "python", "javascript", "expression", "eval", "exec"}
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise IRSchemaError(f"{path} keys must be text")
            normalized = "".join(character for character in key.casefold() if character.isalnum() or character == "_")
            if normalized in forbidden_keys or any(token in normalized for token in ("shader_source", "source_code", "workflow", "provider", "runtime", "executable")):
                raise IRSchemaError("material parameters cannot carry executable shader/provider/workflow source")
            _validate_material_parameters(child, f"{path}.{key}")
    elif isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            _validate_material_parameters(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.casefold()
        if "\n" in value or ";" in value or any(token in lowered for token in ("import ", "def ", "function ", "void main")):
            raise IRSchemaError("material parameter text cannot contain executable source")


@dataclass(frozen=True, order=True)
class MaterialConnectionIR(IRRecord):
    connection_id: str
    source_node_id: str
    source_port_id: str
    target_node_id: str
    target_port_id: str

    def __post_init__(self) -> None:
        for name in ("connection_id", "source_node_id", "source_port_id", "target_node_id", "target_port_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        if self.source_node_id == self.target_node_id and self.source_port_id == self.target_port_id:
            raise IRIntegrityError("material port cannot connect to itself")


@dataclass(frozen=True, order=True)
class MaterialTerminalIR(IRRecord):
    terminal_kind: str
    node_id: str
    port_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_kind, str) or self.terminal_kind not in {"SURFACE", "VOLUME", "DISPLACEMENT", "EMISSION"}:
            raise IRSchemaError("unknown material terminal kind")
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))


@dataclass(frozen=True)
class MaterialGraphIR(IRRecord):
    graph_id: str
    nodes: tuple[MaterialNodeIR, ...]
    connections: tuple[MaterialConnectionIR, ...]
    terminals: tuple[MaterialTerminalIR, ...]
    graph_version: str = "material-graph-v1"

    NESTED: ClassVar = {"nodes": many(MaterialNodeIR), "connections": many(MaterialConnectionIR), "terminals": many(MaterialTerminalIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "graph_version", require_version(self.graph_version))
        nodes = tuple(MaterialNodeIR.coerce(item, "nodes[]") for item in self.nodes)
        node_map = {item.node_id: item for item in nodes}
        if len(node_map) != len(nodes):
            raise IRIntegrityError("material graph node ids must be unique")
        if not nodes:
            raise IRSchemaError("material graph requires at least one typed node")
        connections = tuple(MaterialConnectionIR.coerce(item, "connections[]") for item in self.connections)
        if len({item.connection_id for item in connections}) != len(connections):
            raise IRIntegrityError("material connection ids must be unique")
        input_types: dict[tuple[str, str], str] = {}
        for node in nodes:
            for port in node.ports:
                if port.direction == "input":
                    input_types[(node.node_id, port.port_id)] = port.value_type
        connected_inputs: set[tuple[str, str]] = set()
        adjacency = {node.node_id: set() for node in nodes}
        for connection in connections:
            source = node_map.get(connection.source_node_id)
            target = node_map.get(connection.target_node_id)
            if source is None or target is None:
                raise IRIntegrityError("material connection has dangling node ref")
            source_port = next((port for port in source.ports if port.port_id == connection.source_port_id), None)
            target_port = next((port for port in target.ports if port.port_id == connection.target_port_id), None)
            if source_port is None or target_port is None or source_port.direction != "output" or target_port.direction != "input":
                raise IRIntegrityError("material connection must join a declared output to a declared input")
            if source_port.value_type != target_port.value_type:
                raise IRIntegrityError("material connection port types differ")
            key = (target.node_id, target_port.port_id)
            if key in connected_inputs:
                raise IRIntegrityError("material input port has multiple incoming connections")
            connected_inputs.add(key)
            adjacency[source.node_id].add(target.node_id)
        _acyclic(adjacency)
        terminals = tuple(MaterialTerminalIR.coerce(item, "terminals[]") for item in self.terminals)
        if len({item.terminal_kind for item in terminals}) != len(terminals):
            raise IRSchemaError("material graph terminal kinds must be unique")
        for terminal in terminals:
            node = node_map.get(terminal.node_id)
            if node is None or not any(port.port_id == terminal.port_id and port.direction == "output" for port in node.ports):
                raise IRIntegrityError("material terminal references an undeclared output")
        required_inputs = {(node.node_id, port.port_id) for node in nodes for port in node.ports if port.direction == "input" and port.requirement is RequirementLevel.REQUIRED}
        # Unconnected required inputs are valid only when the node declares a typed parameter for them.
        for node_id, port_id in required_inputs - connected_inputs:
            node = node_map[node_id]
            if node.parameters is None or port_id not in node.parameters:
                raise IRIntegrityError(f"required material input {node_id}.{port_id} is neither connected nor explicitly parameterized")
        object.__setattr__(self, "nodes", tuple(sorted(nodes, key=lambda item: item.node_id)))
        object.__setattr__(self, "connections", tuple(sorted(connections, key=lambda item: item.connection_id)))
        object.__setattr__(self, "terminals", tuple(sorted(terminals, key=lambda item: item.terminal_kind)))

    @property
    def digest(self) -> str:
        return content_digest(self.to_payload())


def _acyclic(adjacency: Mapping[str, set[str]]) -> None:
    active: set[str] = set()
    done: set[str] = set()

    def walk(node: str) -> None:
        if node in active:
            raise IRIntegrityError("material graph contains a cycle")
        if node in done:
            return
        active.add(node)
        for child in sorted(adjacency[node]):
            walk(child)
        active.remove(node)
        done.add(node)

    for node in sorted(adjacency):
        walk(node)


@dataclass(frozen=True)
class MaterialIR(IRRecord):
    material_id: str
    graph: MaterialGraphIR
    semantic_refs: tuple[SemanticRef, ...]
    extensions: tuple[str, ...] = ()

    NESTED: ClassVar = {"graph": one(MaterialGraphIR), "semantic_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "material_id", require_identifier(self.material_id, "material_id"))
        object.__setattr__(self, "graph", MaterialGraphIR.coerce(self.graph, "graph"))
        refs = tuple(SemanticRef.coerce(item, "semantic_refs[]") for item in self.semantic_refs)
        if not refs:
            raise IRAdmissionError("material semantics require admitted source refs")
        object.__setattr__(self, "semantic_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        object.__setattr__(self, "extensions", identifiers(self.extensions, "extensions"))


@dataclass(frozen=True)
class MaterialBindingIR(IRRecord):
    binding_id: str
    material_id: str
    target_ref: IRNodeRef
    purpose: str
    subset_id: str | None = None
    fidelity_tier: str = "final"
    satisfies_final_obligation: bool = False
    obligation_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"target_ref": one(IRNodeRef), "obligation_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        for name in ("binding_id", "material_id", "purpose"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        object.__setattr__(self, "fidelity_tier", require_identifier(self.fidelity_tier, "fidelity_tier"))
        object.__setattr__(self, "target_ref", IRNodeRef.coerce(self.target_ref, "target_ref"))
        if self.subset_id is not None:
            object.__setattr__(self, "subset_id", require_identifier(self.subset_id, "subset_id"))
        if self.fidelity_tier not in {"preview", "final"}:
            raise IRSchemaError("fidelity_tier must be preview or final")
        refs = tuple(SemanticRef.coerce(item, "obligation_refs[]") for item in self.obligation_refs)
        object.__setattr__(self, "obligation_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        if not isinstance(self.satisfies_final_obligation, bool):
            raise IRSchemaError("satisfies_final_obligation must be bool")
        if self.fidelity_tier == "preview" and self.satisfies_final_obligation:
            raise IRAdmissionError("preview material binding cannot satisfy final obligations by default")
        if self.satisfies_final_obligation and not self.obligation_refs:
            raise IRAdmissionError("final obligation satisfaction requires explicit M01 obligation refs")


@dataclass(frozen=True)
class ColorValueIR(IRRecord):
    components: tuple[float, ...]
    color_space: str
    encoding: str
    alpha_mode: str = "opaque"
    semantic_ref: SemanticRef | None = None

    NESTED: ClassVar = {"semantic_ref": optional(SemanticRef)}

    def __post_init__(self) -> None:
        components = tuple(float(require_finite_number(value, "components[]")) for value in self.components)
        if len(components) not in {3, 4}:
            raise IRSchemaError("ColorValueIR requires RGB or RGBA components")
        object.__setattr__(self, "components", components)
        object.__setattr__(self, "color_space", require_identifier(self.color_space, "color_space"))
        object.__setattr__(self, "encoding", require_identifier(self.encoding, "encoding"))
        object.__setattr__(self, "alpha_mode", require_identifier(self.alpha_mode, "alpha_mode"))
        if self.alpha_mode not in {"opaque", "straight", "premultiplied"} or (self.alpha_mode == "opaque" and len(components) == 4 and components[3] != 1.0):
            raise IRSchemaError("alpha semantics are inconsistent with components")
        if self.semantic_ref is not None:
            object.__setattr__(self, "semantic_ref", SemanticRef.coerce(self.semantic_ref, "semantic_ref"))


@dataclass(frozen=True)
class ColorPipelineRef(IRRecord):
    reference: ExternalIdentityRef

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        ref = ExternalIdentityRef.coerce(self.reference, "reference")
        if ref.authority != "m38.color_pipeline":
            raise IRSchemaError("ColorPipelineRef must remain an opaque M38 reference")
        object.__setattr__(self, "reference", ref)


@dataclass(frozen=True)
class ColorConversionReceipt(IRRecord):
    receipt_id: str
    source_digest: str
    result_digest: str
    pipeline: ColorPipelineRef
    policy_ref: SemanticRef
    conversion_version: str

    NESTED: ClassVar = {"pipeline": one(ColorPipelineRef), "policy_ref": one(SemanticRef)}

    def __post_init__(self) -> None:
        from .versions import require_digest
        object.__setattr__(self, "receipt_id", require_identifier(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "source_digest", require_digest(self.source_digest, "source_digest"))
        object.__setattr__(self, "result_digest", require_digest(self.result_digest, "result_digest"))
        object.__setattr__(self, "pipeline", ColorPipelineRef.coerce(self.pipeline, "pipeline"))
        object.__setattr__(self, "policy_ref", SemanticRef.coerce(self.policy_ref, "policy_ref"))
        object.__setattr__(self, "conversion_version", require_version(self.conversion_version))
