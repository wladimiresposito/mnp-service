% 40_exceptions.lp
% Exceptions are supplied as facts:
%
% emergency_exception(U,P).
% human_review_override(U,P).

requires_escalation(U,P) :-
    forbidden(process_sensitive_data(U,P),_),
    not human_review_override(U,P),
    not emergency_exception(U,P).

#show requires_escalation/2.

% Incidente de dados (data_breach) escala para revisao humana,
% independentemente de proibicao (acionar DPO, avaliar notificacao,
% Art. 48 LGPD). Alinha com o fallback Python (descoberto via teste
% diferencial sintetico).
requires_escalation(U,P) :-
    happens(data_breach(U,P),T0),
    current_time(CT),
    T0 <= CT,
    subject(U),
    purpose(P).
