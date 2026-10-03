# Security

Agent Change Proposals works with traces, prompts, outputs, eval labels, and
incident-like outcome signals. These can contain sensitive data.

## Reporting Security Issues

Please report security issues privately by emailing the maintainer listed in the
GitHub profile, or by using GitHub private vulnerability reporting if it is
enabled for this repository.

Do not open a public issue containing:

- customer data;
- private prompts, tool arguments, or model outputs;
- proprietary traces or eval exports;
- API keys, tokens, secrets, or internal URLs;
- regulated or safety-sensitive user content.

## Sharing Fixtures

When opening public issues, provide the smallest sanitized fixture that
reproduces the behavior. Replace real user text, account identifiers, document
contents, tool payloads, and business-sensitive labels with synthetic values.

If a bug cannot be explained without sensitive data, describe the shape of the
data and the failing command instead of pasting the data itself.
