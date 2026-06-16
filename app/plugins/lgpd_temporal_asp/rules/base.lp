% Experimental Event Calculus-style ASP rules for temporal consent.
%
% This is intentionally small and demonstrative. It models active consent as
% a fluent initiated by grant_consent and terminated by revoke_consent.

initiates(grant_consent(U,P), consent(U,P), T) :-
    subject(U), purpose(P), time(T).

terminates(revoke_consent(U,P), consent(U,P), T) :-
    subject(U), purpose(P), time(T).

holds_at(F,T) :-
    time(T),
    happens(E,T0),
    initiates(E,F,T0),
    T0 < T,
    not clipped(T0,F,T).

clipped(T0,F,T) :-
    time(T),
    time(T0),
    happens(E,T1),
    terminates(E,F,T1),
    T0 < T1,
    T1 < T.

forbidden(process_health_data(U,P),T) :-
    current_time(T),
    candidate_process(U,P),
    sensitive_health_data(U),
    not holds_at(consent(U,P),T).

required_change(obtain_active_consent) :-
    forbidden(process_health_data(_,_),_).

required_change(confirm_purpose) :-
    forbidden(process_health_data(_,_),_).

required_change(avoid_processing_sensitive_data_until_allowed) :-
    forbidden(process_health_data(_,_),_).

#show holds_at/2.
#show clipped/3.
#show forbidden/2.
#show required_change/1.
