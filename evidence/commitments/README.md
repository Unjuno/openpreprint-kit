# Anonymized private-record commitments

This directory is **public** in a Public Repository. Place only JSON receipts
created by `python scripts/private_seal.py seal ...` here. The generated
receipts reveal only a random ID and HMAC-SHA256 commitment; they contain
no medical content, filename, patient identifier, salt, or secret key.

**Never commit** raw medical/health records, individual-level sensitive data,
consent forms or HMAC key files. Keep records and per-record keys outside the
repository in access-controlled storage. If you accidentally push confidential
information to GitHub, treating a deleted commit as complete deletion is unsafe.

HMAC receipts prove matching to parties who are given the correct original
and key. Timestamping the Release manifest can establish existence by an upper
bound subject to trusted TSA rules, not authorship, patient identity, clinical
truth or the record's first public availability. Key loss makes selective
verification impossible; a leaked key reduces confidentiality guarantees.
