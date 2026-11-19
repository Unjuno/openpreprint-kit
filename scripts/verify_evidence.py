#!/usr/bin/env python3
"""Verify an OPK release and, optionally, an independent timestamped witness.

This command is offline. The caller must supply out-of-band trust material.
A PASS only applies to the explicitly requested evidence scope; it does NOT
prove authorship, scientific truth, witness independence, or first publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from preflight import validate_repository
from observation import VERSION_RE, assert_source_identity, verify_public
from timestamp import load_policy, read_regular, verify_proof
from verify_release import sha256_file, verify


SCOPES = ('existence', 'public-observation')


def verify_all(
    bundle: Path, policy_path: Path, repository: str, version: str, scope: str,
    *, witness: Path | None = None, public_key: Path | None = None,
    public_key_sha256: str | None = None, expected_paper_sha256: str | None = None,
) -> dict:
    """Verify exact Release assets and required third-party evidence, offline.

    `public-observation` means a signed assertion of retrieval, not that a
    software verifier independently established the witness's conduct.
    """
    if scope not in SCOPES:
        raise ValueError('explicit scope must be existence or public-observation')
    validate_repository(repository)
    if (not isinstance(version, str) or not VERSION_RE.fullmatch(version)
            or not any(int(component) for component in version[1:].split('.'))):
        raise ValueError('expected release version must be a published version such as v1')

    has_witness_args = any(item is not None for item in (witness, public_key, public_key_sha256))
    if scope == 'existence' and has_witness_args:
        raise ValueError('witness arguments require public-observation scope')
    if scope == 'public-observation' and any(
        item is None for item in (witness, public_key, public_key_sha256)
    ):
        raise ValueError('public-observation requires witness, trusted public key and its SHA-256 pin')

    problems = verify(bundle, expected_paper_sha256)
    if problems:
        raise ValueError('release integrity failed: ' + '; '.join(problems))
    assert_source_identity(bundle, repository, version)
    policy = load_policy(policy_path)
    release_time = verify_proof(
        bundle, read_regular(bundle / 'timestamp.tsq'),
        read_regular(bundle / 'timestamp.tsr'), policy,
    )

    report = {
        'schema_version': 1,
        'verdict': 'PASS',
        'scope': scope,
        'repository': repository,
        'version': version,
        'paper_sha256': sha256_file(bundle / 'paper.pdf'),
        'manifest_sha256': release_time['manifest_sha256'],
        'content_integrity': 'VERIFIED',
        'existence_time': 'VERIFIED_BY_SELECTED_TSA',
        'existence_tsa_time_utc': release_time['tsa_time_utc'],
        'existence_accuracy_microseconds': release_time['accuracy_microseconds'],
        'public_observation': 'NOT_CHECKED',
        'observation_timestamp': 'NOT_CHECKED',
        'operator_independence': 'NOT_VERIFIED',
        'first_publication': 'NOT_PROVEN',
        'authorship': 'NOT_PROVEN',
        'scientific_correctness': 'NOT_PROVEN',
        'trust_basis': 'SEPARATELY_SELECTED_TSA_POLICY',
    }

    if scope == 'public-observation':
        # The witness verifier re-checks Ed25519, key pin, source identity,
        # the time-stamped signed observation, and the original paper's TSA.
        checked = verify_public(
            witness, public_key, public_key_sha256, policy_path,
            require_observation_timestamp=True,
            expected_repository=repository, expected_version=version,
        )
        if checked['observation_timestamp'] != 'VERIFIED':
            raise ValueError('witness signed receipt was not timestamp-verified')
        observed = witness / 'bundle'
        source_names = {p.name for p in bundle.iterdir()}
        observed_names = {p.name for p in observed.iterdir()}
        if source_names != observed_names:
            raise ValueError('witness observed different release bytes (asset list mismatch)')
        for filename in sorted(source_names):
            source_file = bundle / filename
            observed_file = observed / filename
            if (not source_file.is_file() or source_file.is_symlink()
                    or not observed_file.is_file() or observed_file.is_symlink()
                    or source_file.stat().st_size != observed_file.stat().st_size
                    or sha256_file(source_file) != sha256_file(observed_file)):
                raise ValueError('witness observed different release bytes: ' + filename)
        report.update({
            'public_observation': 'SIGNED_WITNESS_ASSERTION',
            'observation_timestamp': 'VERIFIED',
            'observation_tsa_time_utc': checked['observation_tsa_time_utc'],
            'observation_accuracy_microseconds': checked['observation_accuracy_microseconds'],
            'observed_interval_start_utc': checked['observed_interval_start_utc'],
            'observed_interval_end_utc': checked['observed_interval_end_utc'],
            'observer_public_key_sha256': checked['observer_key_sha256'],
        })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', required=True, choices=SCOPES)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--policy', required=True, type=Path, help='independently selected TSA trust policy')
    parser.add_argument('--repository', required=True, help='expected OWNER/PAPER repository')
    parser.add_argument('--version', required=True, help='expected public Release tag, e.g. v1')
    parser.add_argument('--witness', type=Path)
    parser.add_argument('--observer-public-key', type=Path)
    parser.add_argument('--observer-public-key-sha256')
    parser.add_argument('--expected-paper-sha256')
    args = parser.parse_args()
    try:
        report = verify_all(
            args.bundle, args.policy, args.repository, args.version, args.scope,
            witness=args.witness, public_key=args.observer_public_key,
            public_key_sha256=args.observer_public_key_sha256,
            expected_paper_sha256=args.expected_paper_sha256,
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(json.dumps({
            'verdict': 'FAIL', 'scope': args.scope,
            'error': str(exc)[:1000],
            'first_publication': 'NOT_PROVEN',
            'authorship': 'NOT_PROVEN',
        }, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
