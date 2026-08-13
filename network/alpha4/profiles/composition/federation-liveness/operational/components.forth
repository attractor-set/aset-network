: REQUIRED-CAPABILITIES-SATISFIED?  ( provided -- flag )                                         LIVENESS-REQUIRED-CAPABILITIES SUBSET-OF? ;
: COMPOSITION-BOUNDARY-PRESERVED?   ( parent state-xfer transition-xfer authority-xfer -- flag ) NO-PROFILE-PARENT? NO-STATE-TRANSFER? NO-TRANSITION-TRANSFER? NO-AUTHORITY-TRANSFER? AND AND AND ;
: DELIVERY-WITNESS?                 ( exported delivered export -- flag )                        EXPORTED? DELIVERED? AND ;
: OBSERVATION-WITNESS?              ( delivered observed export -- flag )                        DELIVERED? OBSERVED? AND ;
: RESOLUTION-WITNESS?               ( observed resolved export -- flag )                         OBSERVED? RESOLVED? AND ;
: PROGRESS-WITNESS?                 ( exported delivered observed resolved export -- flag )      DELIVERY-WITNESS? OBSERVATION-WITNESS? RESOLUTION-WITNESS? AND AND ;
