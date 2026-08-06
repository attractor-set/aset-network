# Security and privacy profiles

The federation-recognition core is cryptographically neutral. Implementations must bind a separately versioned security profile declaring at least identity proof, signature verification, replay protection, key custody, revocation, transport confidentiality and audit retention.

Homomorphic encryption is a valid future privacy profile for inter-federative or metafederative computation over private inputs. Such a profile must preserve local sovereignty: joint computation does not create a superior Context, and every participant retains local authority to recognize or reject the resulting Outcome.
