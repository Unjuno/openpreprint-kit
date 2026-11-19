"""Strict safe YAML loading for research disclosure and citation metadata.

PyYAML SafeLoader silently keeps the final value of repeated mapping keys.
Fail closed on duplicate keys rather than guessing which approval was intended.
"""
from __future__ import annotations

import yaml
from yaml.constructor import ConstructorError


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise ConstructorError(None, None, "expected a mapping", node.start_mark)
        self.flatten_mapping(node)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ConstructorError(None, None, "YAML mapping keys must be strings", key_node.start_mark)
            if key in mapping:
                raise ConstructorError(None, None, "duplicate YAML mapping key: " + key, key_node.start_mark)
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def safe_load_unique(stream):
    """Return YAML data, rejecting duplicate mapping keys at every depth."""
    return yaml.load(stream, Loader=UniqueKeyLoader)
