% 20_lgpd_fluents.lp
% LGPD-inspired fluents.

initiates(grant_consent(U,P), consent(U,P), T) :-
    subject(U), purpose(P), time(T).

terminates(revoke_consent(U,P), consent(U,P), T) :-
    subject(U), purpose(P), time(T).

terminates(change_purpose(U,P), consent(U,P), T) :-
    subject(U), purpose(P), time(T).

initiates(grant_consent(U,P), purpose_confirmed(U,P), T) :-
    subject(U), purpose(P), time(T).

terminates(change_purpose(U,P), purpose_confirmed(U,P), T) :-
    subject(U), purpose(P), time(T).

initiates(start_processing(U,P), processing_active(U,P), T) :-
    subject(U), purpose(P), time(T).

terminates(stop_processing(U,P), processing_active(U,P), T) :-
    subject(U), purpose(P), time(T).

sensitive_processing_candidate(U,P,T) :-
    current_time(T),
    candidate_process(U,P),
    data_category(U,C),
    sensitive_category(C).
