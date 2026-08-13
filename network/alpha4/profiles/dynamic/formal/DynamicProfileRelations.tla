---------------------- MODULE DynamicProfileRelations ----------------------
EXTENDS FiniteSets

CONSTANTS Profiles, Contexts, StateRoots, Epochs, Scopes

ASSUME /\ Profiles # {}
       /\ Contexts # {}
       /\ StateRoots # {}
       /\ Epochs # {}
       /\ Scopes # {}

RecognitionValues == {"UNKNOWN", "ALLOW", "BLOCK"}

ProfileBindingType ==
  [profile : Profiles,
   target_context : Contexts,
   target_state_root : StateRoots,
   target_policy_epoch : Epochs,
   seed_scope : Scopes]

SeedBindingType ==
  [context : Contexts,
   state_root : StateRoots,
   question : Profiles,
   policy_epoch : Epochs,
   scope : Scopes]

ProjectSeedBinding(binding) ==
  [context |-> binding.target_context,
   state_root |-> binding.target_state_root,
   question |-> binding.profile,
   policy_epoch |-> binding.target_policy_epoch,
   scope |-> binding.seed_scope]

ProfileApplicable(binding, seedBinding, recognition) ==
  /\ binding \in ProfileBindingType
  /\ seedBinding \in SeedBindingType
  /\ seedBinding = ProjectSeedBinding(binding)
  /\ recognition = "ALLOW"

DynamicProfileNetworkProjection(networkBefore, networkAfter) ==
  networkAfter = networkBefore

=============================================================================
