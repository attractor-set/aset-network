: ADMIT-FRESH     ( imports observation -- imports result )  EXACT-IMPORT? FRESH-ID? ADD-IMPORT IMPORT-ADMITTED ;
: ADMIT-REPLAY    ( imports observation -- imports result )  EXACT-IMPORT? EXACT-REPLAY? KEEP-IMPORTS IDEMPOTENT-REPLAY ;
: REJECT-CONFLICT ( imports observation -- imports result )  EXACT-IMPORT? CONFLICTING-ID? KEEP-IMPORTS IDENTIFIER-CONFLICT ;
