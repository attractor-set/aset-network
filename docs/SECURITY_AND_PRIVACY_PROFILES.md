# Security and privacy profiles

The minimal admission core is cryptographically neutral. Implementations that claim a concrete security profile must separately declare identity proof, signature verification, replay protection, key custody, revocation, transport confidentiality and audit-retention guarantees appropriate to that profile. Federation-specific security requirements belong to the optional Federation Profile or to separate profiles composed with it, not to the universal Network core.

Homomorphic encryption remains a valid future privacy profile for inter-federative or metafederative computation over private inputs. Such a profile must preserve local sovereignty: joint computation does not create a superior Context, and every participant retains target-local Seed authority over recognition of resulting evidence or outcomes.
