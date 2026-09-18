# Retained YouTrack deployment

This is the minimal retained deployment: one pinned YouTrack container and one
pinned Caddy reverse proxy. Caddy obtains and renews a dedicated Let's Encrypt
certificate with a Route53 DNS-01 challenge. YouTrack is available only through
the proxy.

## Host layout

```text
/opt/devtools-youtrack/             deployment checkout
/etc/devtools-youtrack/route53.env  root-only TLS credentials
/srv/devtools-youtrack/             persistent application and proxy data
```

The four YouTrack directories under `/srv/devtools-youtrack` must be owned by
`13001:13001`. The Caddy directories can remain root-owned; its container manages
their contents.

## Required human inputs

- Decide whether the instance starts empty or is restored from an authorised backup.
- Create `dev-tools.helix-onprem.net` as an A record for the retained private IP.
- Create a dedicated AWS access key using `route53-iam-policy.json`. It is restricted
  to the observed `helix-onprem.net` hosted zone and this hostname's ACME TXT record.
- Supply the AWS key in `/etc/devtools-youtrack/route53.env`; do not put it in Git or
  chat.
- Decide backup schedule, local retention, off-host destination, failure notification,
  and restore-rehearsal cadence.

Do not create a permanent `_acme-challenge` TXT record. Caddy creates and removes
the value required for each certificate issue or renewal.

## Install and start

From this directory on the retained host:

```bash
sudo install -d -m 0755 /srv/devtools-youtrack/{data,conf,logs,backups,caddy-data,caddy-config}
sudo chown -R 13001:13001 /srv/devtools-youtrack/{data,conf,logs,backups}
sudo install -d -m 0700 /etc/devtools-youtrack
sudo install -m 0600 route53.env /etc/devtools-youtrack/route53.env
sudo docker compose config --quiet
sudo docker compose build --pull caddy
sudo docker compose up -d
```

The source `route53.env` in the example above is an operator-created temporary file;
remove it after installation. Verify with:

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 caddy
curl --fail --show-error --head https://dev-tools.helix-onprem.net
```

Complete the YouTrack configuration wizard at that HTTPS URL and set its base URL to
`https://dev-tools.helix-onprem.net`. Then apply the project, restricted identities,
workflow, readiness field, backup and notification settings from
`docs/retained-deployment-handoff.md`.

## Create a project

The retained instance has one custom project template, `HELIXTPL`. It carries the
standard State values and transitions, the raw State mutation guard, and the Agent
Readiness field/reset rule. Install the small bootstrap script on the host with:

```bash
sudo install -o root -g root -m 0755 bootstrap-project.py \
  /usr/local/sbin/youtrack-bootstrap-project
```

Run it interactively:

```bash
sudo /usr/local/sbin/youtrack-bootstrap-project
```

It asks for a project name, key, optional description, and confirmation. It creates
the project through YouTrack's supported REST API using `HELIXTPL`, then verifies the
State and Agent Readiness values and defaults. While the temporary administrator
bootstrap token exists, the script reads its root-only file. After that token is
removed, it securely prompts for a permanent token belonging to a user with the
Project Creator role. The token owner becomes the new project's owner.

The template is the configuration source of truth. Changes to it affect only projects
created afterwards; update existing projects separately when a workflow changes.

## Routine operations

```bash
sudo docker compose pull youtrack
sudo docker compose build --pull caddy
sudo docker compose up -d
sudo docker compose logs --tail=100
sudo docker compose down
```

Do not run `down --volumes` and do not delete `/srv/devtools-youtrack`. Upgrades need
their own reviewed change to the pinned image versions plus a verified backup first.
