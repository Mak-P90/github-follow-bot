# Hardened container runtime profile (baseline)

- Run as non-root (`USER 65532:65532`).
- Mount application root filesystem as read-only.
- Mount writable tmpfs only for `/tmp` and runtime socket paths.
- Apply seccomp profile from `deploy/security/seccomp-profile.json`.
- Apply AppArmor profile from `deploy/security/apparmor-profile.txt`.
- Restrict egress to:
  - `api.github.com:443`
  - OTel collector endpoint
  - Queue backend endpoint (RabbitMQ/SQS bridge)

See `deploy/security/egress-allowlist.yaml` for template.
