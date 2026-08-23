# Security policy

AUREUS is fail-closed.

## Never commit

API keys, passwords, wallet/private keys, payout identifiers, `.env` files, OpenBao tokens, database credentials or private TLS material.

## Critical-action policy

Critical financial, identity, contractual or provider-mutation actions cannot be authorized solely by probabilistic model output. They require deterministic policy checks and explicit approval when applicable.

## Forbidden behavior

Cryptojacking, unauthorized compute use, CAPTCHA/anti-bot bypass, identity/KYC falsification, credential harvesting, payment manipulation and evasion of platform restrictions are prohibited.

Report security issues privately to the repository owner.
