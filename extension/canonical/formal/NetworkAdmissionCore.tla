------------------------ MODULE NetworkAdmissionCore ------------------------
EXTENDS NetworkExtensionTLC

(***************************************************************************
Compatibility name retained from the alpha.2 shadow-extraction slice.
As of alpha.3, NetworkExtension itself IS the minimal admission core.
***************************************************************************)

AdmissionCoreSpec == SafetySpec
AdmissionCoreSafety == MinimalNetworkSafety

=============================================================================
