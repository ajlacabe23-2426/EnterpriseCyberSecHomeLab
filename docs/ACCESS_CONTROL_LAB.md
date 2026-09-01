# Exercise 2 — Prove least privilege with allow and deny tests

## Outcome

A standard user can perform the intended operation in their department's test area, while a different standard user is denied that operation. Both results are necessary.

## Inspect first on DC01

Run `Start-Lab.ps1 -Role DC` elevated. It lists group membership, share ACLs, NTFS ACLs and broad share identities. `Authenticated Users: Change` on a share is broad, but restrictive NTFS permissions may still deny effective access. An ACL listing is not the final test.

Draft the intended policy before editing anything:

| Share | Department group to review | Standard member | Standard nonmember |
|---|---|---|---|
| AtlasIQ-Finance | GG-AtlasIQ-Finance | Select from current report | Verify absent from this group and privileged groups |
| AtlasIQ-Executives | GG-AtlasIQ-Executives | ecarter only if current membership confirms | Select verified nonmember |
| AtlasIQ-IT | GG-AtlasIQ-IT-Admins | Review whether members are privileged before testing | Select verified nonmember |
| AtlasIQ-Security | GG-AtlasIQ-Security-Analysts | Select from current report | Select verified nonmember |
| AtlasIQ-Public | GG-AtlasIQ-Standard-Users | Define intended read/write policy first | Define intended unaffiliated access first |

Do not infer membership from a person's name. IT-Admins group membership is not automatically Domain Admin membership; inspect nested/effective memberships too.

## Test one department end to end

1. Choose two existing standard test accounts, one intended member and one nonmember. Verify `whoami /groups` and avoid Domain Admin sessions.
2. Use a clearly named disposable test folder/file within the department share, created by an authorized user. Record its ACL inheritance. Use only test content.
3. Sign in to the Windows client as the allowed account. Access the share by DC FQDN, not IP, to preserve the normal domain authentication path. Test list/read and, if policy permits, create/edit/delete only the disposable test file.
4. Fully sign out. Sign in as the nonmember and repeat the same operation and exact path. Do not mix alternate SMB credentials in one session; existing connections can reuse credentials.
5. Record the exact result and error. A network timeout or nonexistent path is not proof of an authorization denial. Confirm the target still works for the allowed user.

Example path to inspect:

```powershell
Get-ChildItem '\\DC01.atlasiqlab.local\AtlasIQ-Finance' -ErrorAction Stop
```

For a positive write test, use a new uniquely named text file within the disposable test area; never replace existing data. Deny tests should be run by a person after checking the account, target and intended policy.

## If the results show a permission problem

- Preserve the current share ACL and NTFS ACL before a change; take a relevant VM snapshot only if storage allows and document what it covers.
- Add/verify the intended department group access first. Keep administrative recovery access.
- Remove only the confirmed unnecessary broad share grant; do not recursively replace NTFS permissions or add blanket Deny entries.
- Share and NTFS checks both apply over SMB. A Deny ACE can override intended allows and complicate nesting; prefer a deliberate allow model.
- Sign out/in after group membership changes so the user token refreshes, and repeat both tests.
- If an authorized user loses access, restore the exact prior grant from the recorded ACL and recheck.

No automatic ACL mutation is provided because the current effective memberships and policy have not been verified on the machine.

## Explain it back

Authentication answers who you are. Authorization answers which operation you may perform on which resource. Why does a successful domain login not imply access to the Finance share? Why does denying a nonexistent file prove nothing?

## Evidence and exit gate

Capture the account/group context, exact resource, allowed operation, denied operation, before/after ACLs if changed, and retest. Redact personal identifiers before adding a short summary to the public repo. Repeat for each department after the first test is correct.
