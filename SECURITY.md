# Security

## Reporting a vulnerability

Please report security problems privately through GitHub: open the
repository's **Security** tab and choose **Report a vulnerability**. Don't
open a public issue for them.

Olde is a small personal project maintained in spare time, so there's no
guaranteed response time, but reports are read and fixes go to the `main`
branch.

## Scope

Olde is meant to run on your own computer and listens only on `127.0.0.1`.
Useful reports include:

- feed content that can inject markup or script into the page
- a way to make Olde read or write files outside its state file
- secrets or personal data showing up in logs, the page or the state file
- a vulnerable dependency that Olde actually uses

Exposing Olde to a network yourself (for example by changing the host it binds
to) is outside what it's designed for.
