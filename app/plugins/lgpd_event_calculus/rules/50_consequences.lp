% 50_consequences.lp
% Consequences.

consequence(processing_must_be_modified_or_stopped) :-
    forbidden(process_sensitive_data(_,_),_).

% Breach conta se ocorreu ATE current_time (inclusive), nunca no futuro.
% A regra anterior nao tinha guarda de tempo e contava ate breach futuro
% (bug pego pelo teste diferencial sintetico).
consequence(breach_response_required) :-
    happens(data_breach(U,P),T0),
    current_time(CT),
    T0 <= CT.

obligation(obl_log_and_notify_breach) :-
    happens(data_breach(U,P),T0),
    current_time(CT),
    T0 <= CT.

#show consequence/1.
