% 30_obligations.lp
% Obligations and violations.
%
% FIX (item 2): cada violated_rule/required_change deve estar amarrado a
% sua condicao especifica de proibicao, e nao ao predicado generico
% forbidden/2. Antes, "ec_purpose_not_confirmed" disparava para QUALQUER
% proibicao, inclusive quando a causa real era ausencia de consentimento.

% ----- Proibicao por ausencia de base legal (consentimento) -----
forbidden_no_consent(process_sensitive_data(U,P),T) :-
    sensitive_processing_candidate(U,P,T),
    requires_legal_basis,
    not holds_at(consent(U,P),T),
    not emergency_exception(U,P),
    not human_review_override(U,P).

% ----- Proibicao por ausencia de confirmacao de proposito -----
forbidden_no_purpose(process_sensitive_data(U,P),T) :-
    sensitive_processing_candidate(U,P,T),
    requires_purpose_confirmation,
    not holds_at(purpose_confirmed(U,P),T),
    not emergency_exception(U,P),
    not human_review_override(U,P).

% ----- forbidden/2 generico deriva de qualquer das causas -----
forbidden(A,T) :- forbidden_no_consent(A,T).
forbidden(A,T) :- forbidden_no_purpose(A,T).

% ----- Violacoes amarradas a causa especifica -----
violated_rule(ec_sensitive_processing_without_active_consent) :-
    forbidden_no_consent(process_sensitive_data(_,_),_).

violated_rule(ec_purpose_not_confirmed) :-
    forbidden_no_purpose(process_sensitive_data(_,_),_).

% ----- Mudancas exigidas amarradas a causa especifica -----
required_change(obtain_active_consent) :-
    forbidden_no_consent(process_sensitive_data(_,_),_).

required_change(avoid_processing_sensitive_data_until_allowed) :-
    forbidden(process_sensitive_data(_,_),_).

required_change(confirm_purpose) :-
    forbidden_no_purpose(process_sensitive_data(_,_),_).

% ----- Obrigacoes derivadas das violacoes -----
obligation(obl_obtain_active_consent) :-
    violated_rule(ec_sensitive_processing_without_active_consent).

obligation(obl_confirm_purpose) :-
    violated_rule(ec_purpose_not_confirmed).

#show forbidden/2.
#show violated_rule/1.
#show required_change/1.
#show obligation/1.
