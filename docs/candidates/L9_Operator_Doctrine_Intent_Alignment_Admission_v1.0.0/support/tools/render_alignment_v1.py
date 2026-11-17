#!/usr/bin/env python3
"""Local preview generator/checker; NOT an L9 projection producer or access-control service."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2] / "repo-overlay"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def resolve(obj, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/") or "//" in pointer:
        raise ValueError("invalid JSON pointer")
    current = obj
    for raw in pointer[1:].split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise ValueError("unresolved JSON pointer " + pointer)
        current = current[part]
    return current


def build():
    profile = load("strategy/alignment/operator_alignment.profile.yaml")
    views = load("strategy/alignment/agent_views.yaml")
    if profile["pack_revision"] != "1.0.0":
        raise ValueError("candidate pack revision mismatch")
    originals = {}
    for name, spec in profile["source_instances"].items():
        path = spec["path"]
        if name not in ("doctrine", "intent") or not path.startswith("strategy/"):
            raise ValueError("unexpected operator source")
        blob = (ROOT / path).read_bytes()
        source = yaml.safe_load(blob)
        if digest(blob) != spec["sha256"] or source["revision"] != spec["revision"]:
            raise ValueError("source integrity mismatch for " + name)
        field = "doctrine_ref" if name == "doctrine" else "intent_ref"
        if (
            source[field] != spec["ref"]
            or source["approval"][
                "effective_as_repository_source_only_after_authorized_adoption"
            ]
            is not True
        ):
            raise ValueError(
                "source identity or approval boundary mismatch for " + name
            )
        originals[name] = source
    binding = originals["intent"]["doctrine_binding"]
    if (
        binding["doctrine_ref"] != originals["doctrine"]["doctrine_ref"]
        or binding["doctrine_revision"] != originals["doctrine"]["revision"]
    ):
        raise ValueError("Intent-to-Doctrine exact reference mismatch")
    if set(views["views"]) != {
        "planner",
        "meta_planner",
        "cto",
        "architect",
        "coding_agent",
    }:
        raise ValueError("unexpected role view inventory")
    permitted = profile["selection_policy"]["privileged_selector_allowlist"]
    result = {}
    for name, spec in views["views"].items():
        privileged = name != "coding_agent"
        if spec["privileged"] is not privileged:
            raise ValueError("role privilege mismatch " + name)
        preview = {
            "artifact_kind": "candidate_local_preview_not_producer_projection",
            "authority_class": "derived_non_authoritative",
            "view_ref": spec["view_ref"],
            "role": name,
            "can_activate": False,
            "runtime_receipt": None,
            "global_profile_refs": spec["global_profiles"],
            "additional_runtime_context_needed": spec["external_context"],
            "decision_questions": spec["decision_questions"],
            "forbidden": spec["cannot"],
        }
        if privileged:
            selection = {}
            for source_key, path_key in (
                ("doctrine", "doctrine_paths"),
                ("intent", "intent_paths"),
            ):
                requested = spec[path_key]
                if len(requested) != len(set(requested)):
                    raise ValueError("duplicate privileged selector " + name)
                allowed = set(permitted[source_key])
                if not set(requested).issubset(allowed):
                    raise ValueError("privileged selector not allowed for " + name)
                if any(
                    p == "/core_values"
                    or p.startswith("/additional_core_value_candidates")
                    for p in requested
                ):
                    raise ValueError("unapproved value selector forbidden")
                selection[source_key] = {
                    p: resolve(originals[source_key], p) for p in requested
                }
            preview["selected_operator_sections"] = selection
            preview["source_revision_refs"] = {
                k: p["ref"] + "@" + p["revision"]
                for k, p in profile["source_instances"].items()
            }
            preview["source_sha256"] = {
                k: p["sha256"] for k, p in profile["source_instances"].items()
            }
            preview["access_assurance"] = "not_tested_preview_only"
        else:
            if spec["doctrine_paths"] or spec["intent_paths"]:
                raise ValueError("coding agent has raw operator source selections")
            seen = set()
            obligations = []
            for rule in spec["delegated_obligations"]:
                if rule["id"] in seen:
                    raise ValueError("duplicate coding obligation id")
                seen.add(rule["id"])
                if rule["source"] not in ("doctrine", "intent"):
                    raise ValueError("unexpected coding obligation source")
                value = resolve(originals[rule["source"]], rule["pointer"])
                if not isinstance(value, str):
                    raise ValueError("obligation source must be a string leaf")
                if digest(value.encode("utf-8")) != rule["source_value_sha256"]:
                    raise ValueError("obligation source value digest mismatch")
                quote = rule["evidence_quote"]
                if not quote or quote not in value:
                    raise ValueError("obligation evidence quote mismatch")
                if (
                    rule["summary_review_state"]
                    != "candidate_requires_operator_review_before_delegation"
                ):
                    raise ValueError("unapproved obligation silently promoted")
                obligations.append({"id": rule["id"], "summary": rule["summary"]})
            preview["delegated_obligations"] = obligations
            preview["example_only_no_task_contract_attached"] = True
            preview["trusted_upstream_required"] = True
            preview["access_assurance"] = "not_tested_storage_acl_required"
            # Neither exact private source identities nor their JSON pointers enter the worker preview.
        result[name] = (
            json.dumps(preview, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="read-only check of stored generated bytes"
    )
    args = parser.parse_args()
    previews = build()
    output = ROOT.parent / "support/previews"
    if not args.check:
        output.mkdir(parents=True, exist_ok=True)
    for name, text in previews.items():
        path = output / (name + ".preview.json")
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                raise ValueError("preview mismatch " + name)
        else:
            path.write_text(text, encoding="utf-8")
    print(
        ("Checked" if args.check else "Rendered") + " five candidate-only role previews"
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
