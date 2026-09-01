# Digital Footprint Cleanup signed updates

This is the local source tree for the public `digital-footprint-cleanup-updates`
TUF repository. It was created from the official TUF-on-CI v0.20.0 template.
The workflows and local signer use TUF-on-CI's verified post-0.20 compatibility
commit for patched python-tuf 7.

Current state: **ready for the first signing event, nothing published**. All 33
UK/EU-EEA/US/China jurisdiction packs and their hash manifest pass the unsigned
pre-signing gate. Publication remains fail-closed until TUF-on-CI has generated
and signed the repository metadata. Do not copy a generated root into the client
until the initial signing event and a clean-room root verification have both
succeeded.

## Security model

- Root and delegated target roles are approved through TUF-on-CI signing events.
- Snapshot and timestamp use the selected protected Sigstore online identity.
- The application bundles a read-only initial root and uses python-tuf 7.0.0.
- Targets are delegated by prefix: `catalogue`, `adapters`, `jurisdictions`,
  `datasets`, and `tools`.
- Every target carries signed `custom` metadata matching `feed-manifest.json`.
- Publication stops if one supported jurisdiction code is missing, a source is stale,
  a target hash differs, metadata lacks custom version data, or a sequence rolls
  back.

## Maintainer bootstrap

1. Create the public GitHub repository from this official-template-derived tree
   and add it as this clone's `origin` remote.
2. Enable GitHub Pages from Actions, restrict the `github-pages` environment to
   the `publish` branch, enable protected signing-event pull requests, and give
   workflows only the permissions documented by TUF-on-CI.
3. Copy `.tuf-on-ci-sign.ini.example` to the ignored local configuration file
   and enter the real GitHub signer identity and remote.
4. Install the pinned signing environment from `requirements-signing.txt`.
5. Run `tuf-on-ci-delegate sign/init`, select Sigstore for online signing, review
   every role/key/expiry/threshold, and complete the user authentication step.
6. Create delegated roles for the five target prefixes. For a new target, add
   the file and manifest entry, let TUF-on-CI generate its target metadata, run
   `scripts/apply_target_custom.py`, then have the delegated signers review and
   sign the complete change.
7. Run `python -c 'from scripts.validate_feed import validate_targets; print(validate_targets())'`
   before signing. Run `python scripts/validate_feed.py` before publication; it
   must report all 33 packs and exact signed metadata.
8. After the first repository version is published, independently verify root
   version 1 and only then bundle that exact read-only file in the application.

The app never installs directly from GitHub Releases, PyPI, or another upstream.
Those sources may identify candidates; only targets signed by this repository can
be activated on a device.
