
VP-CUBE-0001: Outbound Calls Fail
Category

Cisco CUBE

Symptoms
Users cannot make outbound PSTN calls
Internal calls may work
Calls may fail with fast busy
SIP errors may include 404, 403, 408, 488, 503
Business Impact

High. Users cannot call external numbers.

Initial Questions
Did this ever work before?
When did it stop working?
Was anything changed recently?
Are all outbound calls failing?
Is it only international, mobile, or specific number ranges?
Are inbound calls working?
Is only one site affected?
Which provider is used?
Required Commands
show dial-peer voice summary
show sip-ua status
show run | sec dial-peer
show run | sec voice service voip
show call active voice brief
show logging
Logs Required
debug ccsip messages
Common Root Causes
Dial-peer mismatch
Translation rule issue
Provider routing issue
SIP trunk down
Codec mismatch
DNS issue
Firewall issue
TLS/certificate issue
Evidence Rules
404 generated locally may indicate dial-peer or routing issue.
488 may indicate codec or SDP negotiation issue.
503 from provider may indicate provider-side rejection or service issue.
408 may indicate timeout, firewall, network, or no response.
Verification
Test local outbound call
Test mobile outbound call
Test international outbound call
Confirm inbound still works
Confirm no new CUBE errors
