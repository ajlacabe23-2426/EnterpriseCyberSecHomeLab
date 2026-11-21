# IAM Policy Lab — Week 1 (offline, synthetic)

**Purpose:** Build an explainable identity-security case study that demonstrates authentication evidence, role-based authorization, least privilege, separation of duties, and time-limited elevated access. This is a self-contained simulation, **not an AD/Entra integration, a production policy engine, or evidence that real access was granted**.

## Run without dependencies

On a Mac, Linux workstation, or Windows PC with Python 3.10+:

~~~bash
cd projects/iam-policy-lab
python3 -m iamlab
python3 -m unittest discover -s . -p 'test_*.py' -v
~~~

All sample identities, role names, access requests and timestamps are fictional. No network access, administrative rights, tokens, credentials or third-party services are needed. The code never calls a real IAM system. For privileged requests, the simulator now requires an explicit non-self-target assertion and distinct fictional actor/approver identifiers. These are **self-supplied fixture attributes, not verified identity proofs**; a real authorization service must independently bind them to authenticated identity and approvals.

## Watch / do / explain

1. **Watch:** Run `python3 -m iamlab` and observe the twelve labeled scenarios: basic role-permitted read, unknown role, least-privilege rejection, MFA required, independent approval required, no self-approval, expired elevation, overly long elevation, and compliant short-lived elevation, plus missing target attestation, same-person approval and missing approver identity.
2. **Do:** In `fixtures/synthetic-requests.json`, create a fictional case in which the `auditor` attempts to change a `role_assignment`. Predict the reason code and run tests. Restore the original fixture afterward or update the expected result deliberately.
3. **Explain:** Describe the difference between *authentication* (the independently established actor and MFA proof), *authorization* (role/resource/action match), and *privileged access governance* (approval plus short expiration). Note that the demo accepts supplied attributes for educational purposes and cannot establish their authenticity.
4. **Verify:** Test that removing the MFA flag, removing approval, using a nonexistent role, extending TTL over four hours, or replaying after expiry results in DENY. Capture terminal output without real names or accounts.

## Skills evidence for IAM applications

| Control | Example reason | Portfolio evidence |
| --- | --- | --- |
| RBAC/least privilege | `LEAST_PRIVILEGE_BLOCK` | Role matrix and rejected request |
| Fail-closed behavior | `MALFORMED_REQUEST` / `UNKNOWN_ROLE` | Missing-attribute tests |
| MFA prerequisite | `MFA_REQUIRED` | Negative test |
| Separation of duties | `SELF_APPROVAL_PROHIBITED` | Negative test |
| Temporary elevation | `ACCESS_EXPIRED` / `ELEVATION_TOO_LONG` | Boundary test |
| Independent review | `HUMAN_APPROVAL_REQUIRED` / `APPROVER_IDENTITIES_REQUIRED` | No-approval or missing reviewer test |
| Separation of duties | `SELF_APPROVAL_PROHIBITED` / `SELF_TARGET_STATUS_REQUIRED` | Same-actor reviewer and missing target-attestation tests |

### Suggested interview exercise

> A helpdesk user says an urgent ticket justifies granting administrator access for the rest of the week. What evidence do you ask for? Which controls cannot be waived? Which actions should require a second approver?

Document a safe, policy-grounded answer without performing a live privilege escalation. A job-ready writeup should distinguish the modeled decision, the tests executed, and the additional verified identity/approval sources a real deployment would require.

## Boundaries and next steps

This lab is deliberately independent of the existing homelab 3D map task and uses only Python's standard library. Mac UTM, Active Directory and Entra ID behavior are not tested by these fixtures. Future phases can explore group membership, access reviews, provisioning/deprovisioning events, and policy-as-code with separate authorization and real-host acceptance.
