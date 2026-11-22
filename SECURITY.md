# Security

Please report a vulnerability privately with GitHub's **Report a vulnerability** button on the Security tab, not in a public issue.

The site is static (no server, no sign-in, no cookies). Page code escapes all data it displays; the build reads files with safe
loaders only, never evaluates input, and pins every dependency and GitHub Action to an exact version.
