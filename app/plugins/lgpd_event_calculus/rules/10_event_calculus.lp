% 10_event_calculus.lp
% Minimal Event Calculus axioms.
% FIX: T and T0 must be bound by time/1 to be safe under Clingo grounding.

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

#show holds_at/2.
#show clipped/3.
