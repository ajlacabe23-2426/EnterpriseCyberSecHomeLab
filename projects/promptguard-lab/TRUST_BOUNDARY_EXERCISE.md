# PromptGuard — action boundary exercise (offline)

**Status:** Software teaching exercise. Nothing here is a production policy engine, authenticated IAM source, real agent runtime, or Mac/UTM verification.

## Threat model

A retrieved document, external tool result, or quoted user text might contain instructions that attempt to override an assistant's objectives. **Detecting suspicious text is useful but cannot establish whether a tool operation is authorized.** The existing scanner produces review signals, including known false positives and false negatives. This module models a second, independent authorization boundary.

The example API separates two concepts:

- `source_type` is analyst-selected provenance for the scanner. All source categories are untrusted; it never grants authority.
- `request_origin` and `ApprovedScope` are values supplied by the **fictional test harness**, standing in for a trusted application's control plane. For any real implementation, these must be established from server-side, authenticated identity and approved workflow state, **never** from raw user input, a model's output, retrieved text, or an attacker-controlled tool response.

`assess_action` returns an **ALLOW/DENY simulation verdict only**. It has no tool dispatcher, network client, file writes, model calls, or token issuer. Even `ALLOW` means *a lab policy would permit this action*, not that anything was performed.

## Try it

From `projects/promptguard-lab`:

```bash
python3 -m promptguard.action_boundary_demo
python3 -m unittest discover -s promptguard -p 'test_*.py' -v
```

Study the four printed fictional cases. Compare a legitimate preapproved read, an instruction carried in a tool response, an unapproved change request, and a suspicious document encountered within an approved read workflow. Reports contain only rule identifiers, decisions, and risk labels—not the source payload.

## Guided independent troubleshooting (15–20 minutes)

1. Predict the result when the external `tool_output` claims to be a system message and proposes `example_case/read`. Which condition denies it?
2. Predict the result when an ordinary, benign message requests `example_case/change` through the approved workflow. Does the absence of injection signals permit the change?
3. Change the fictional scope expiry to exactly the fixed test time. What should happen at the boundary?
4. Compare the scan of a privileged-looking sample across `retrieved_document`, `direct_user` and `tool_output`. Why should no source label create authority?
5. Restore the original fixture and run the regression suite. Explain the distinction between scanner triage and policy enforcement without claiming these fixtures simulate real identity proof.

## Control acceptance matrix

| Gate | What the code can verify | What it cannot verify |
| --- | --- | --- |
| Injection screening | Rule matches and risk signals over submitted fictional text | Intent, safety, or detection of every evasion |
| Untrusted-origin boundary | Toy request origin must equal an allowlisted control-plane value | That a real backend assigned the value independently |
| Least privilege | Resource/action pair must match a fictional scope | Real role memberships, target ownership or access-token validity |
| Expiration | UTC `now` must precede fictional scope expiry | Clock integrity, revocation or real-session expiry |
| Evidence privacy | Reports omit submitted text and fictional scope subject | Security of a complete application, logs, or surrounding services |
| Host verification | None; the module uses offline synthetic inputs only | Mac/UTM, AD, Entra, live syslog, or real authorization outcomes |

## Next live-lab gate (separate approval and evidence)

Use the existing <https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/14> IAM policy exercise and <https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/15> Linux identity review draft *after independent review*, then record sanitized Mac/UTM observations. Do not copy simulator decisions into a "verified real access" claim.

Never put real credentials, company data, identity records, or third-party content into test fixtures.
