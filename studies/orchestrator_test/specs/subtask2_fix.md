# Fix: Syslog tag parsing must strip PID suffix

Integration tests fail because the TCP syslog receiver parses raw messages like:
`<30>Feb 10 12:00:00 pihole dnsmasq[1]: query[A] domain.com from 10.0.0.1`

The tag gets extracted as `"dnsmasq[1]"` instead of `"dnsmasq"`. The PiholeParser.can_parse() then fails to match because it checks for exact values like "dnsmasq".

## Fix needed in `parse_syslog_message` in syslog_receiver.py:

When extracting the tag from RFC 3164 format, strip the PID suffix in brackets. If the tag contains `[`, take only the part before `[`.

For example: `"dnsmasq[123]"` → tag should be `"dnsmasq"`.

Do this by splitting on `[` and taking the first part.

Also, make sure the message field contains the text AFTER the colon separator `: `. For input `dnsmasq[1]: query[A] domain.com from 10.0.0.1`, the message should be `query[A] domain.com from 10.0.0.1`.

Remember to put `# agentmon/collectors/syslog_receiver.py` as the first line.
Output the COMPLETE file.
