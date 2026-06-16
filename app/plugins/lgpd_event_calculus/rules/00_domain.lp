% 00_domain.lp
% Domain declarations for the experimental Event Calculus plugin.

sensitive_category(health).
sensitive_category(sensitive).

event_kind(grant_consent).
event_kind(revoke_consent).
event_kind(change_purpose).
event_kind(start_processing).
event_kind(stop_processing).
event_kind(data_breach).
event_kind(human_review_approved).
event_kind(human_review_rejected).
