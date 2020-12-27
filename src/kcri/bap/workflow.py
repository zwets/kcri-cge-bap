#!/usr/bin/env python3
#
# kcri.bap.workflow - Defines the BAP workflow logic.
#
#   This module defines the DEPENDENCIES dict that captures the workflow logic
#   of the current version of the BAP.  It defines this in term of the primitives
#   offered by the pico.workflow.logic module in package picoline.
#
#   The workflow defined herein can be 'dry tested' by running the module from
#   the command line:
#
#       # Depends on picoline, which depends on psutil, so either install
#       # those, or point the PYTHONPATH there, before running this:
#       python3 -m kcri.bap.workflow --help
#
#   Sibling module .services defines the mapping from the Services enum defined
#   below to the shims that wrap the actual backends.  The sibling module .data
#   defines the BAP-specific "blackboard" that gets passed between the services.
#

import pico.workflow.logic
from pico.workflow.logic import ALL, ONE, OPT, OIF, SEQ


### Target definitions
#
#   Define the Params.*, Checkpoints.*, Services.*, and UserTargets.* constants
#   for the BAP.  The classes are subclassed from their synonymous counterparts
#   in the pico.workflow.logic module.

class Params(pico.workflow.logic.Params):
    '''Flags to signal to the Workflow that some input parameter was provided.'''
    READS = 'reads'         # Signals that user has provided fastq files
    CONTIGS = 'contigs'     # Signals that user has provided contigs
    SPECIES = 'species'     # Signals that user has specified the species
    PLASMIDS = 'plasmids'   # Signals that user has specified the plasmids
    REFERENCE = 'reference' # Signals that user has specified a reference genome
    ILLUMINA = 'illumina'   # Signals that fastqs are Illumina reads

class Checkpoints(pico.workflow.logic.Checkpoints):
    '''Internal targets for other targets to depend on.  Useful when a service
       takes an input that could come either from user or as a service output.'''
    CONTIGS = 'contigs'     # Contigs are available either as inputs or from assembly
    SPECIES = 'species'     # Species is known, either from user input or a service
    PLASMIDS = 'plasmids'   # Plasmids are known, either from user input or a service
    REFERENCE = 'reference' # Reference is known, either from user input or a service

class Services(pico.workflow.logic.Services):
    '''Enum that identifies the available services.  Each corresponds to a shim
       (defined in SERVICES below) that performs the input and output wrangling
       and invokes the actual backend.'''
    READSMETRICS = 'ReadsMetrics'
    QUAST = 'Quast'
    SKESA = 'SKESA'
    SPADES = 'SPAdes'
    MLSTFINDER = 'MLSTFinder'
    KCST = 'KCST'
    KMERFINDER = 'KmerFinder'
    GETREFERENCE = 'GetReference'
    RESFINDER = 'ResFinder'
    POINTFINDER = 'PointFinder'
    VIRULENCEFINDER = 'VirulenceFinder'
    PLASMIDFINDER = 'PlasmidFinder'
    PMLSTFINDER = 'pMLSTFinder'
    CGMLSTFINDER = 'cgMLSTFinder'
    CHOLERAEFINDER = 'CholeraeFinder'
    PROKKA = 'PROKKA'

class UserTargets(pico.workflow.logic.UserTargets):
    '''Enum defining the targets that the user can request.'''
    METRICS = 'metrics'
    ASSEMBLY = 'assembly'
    SPECIES = 'species'
    REFERENCE = 'reference'
    MLST = 'mlst'
    RESISTANCE = 'resistance'
    VIRULENCE = 'virulence'
    PLASMIDS = 'plasmids'
    PMLST = 'pmlst'
    CGMLST = 'cgmlst'
    SPECIALISED = 'specialised'
    ANNOTATION = 'annotation'
    DEFAULT = 'DEFAULT'
    FULL = 'FULL'


### Dependency definitions
#
#   This section defines DEPENDENCIES, a dict that maps each target defined above
#   to its dependencies.  See the WorkflowLogic module for the definition of the
#   ALL, ONE, SEQ, OPT, OIF connectors.

DEPENDENCIES = {
    
    UserTargets.METRICS:        ALL( OPT( Services.QUAST ), OPT( Services.READSMETRICS ) ),
    UserTargets.ASSEMBLY:       ONE( Services.SKESA, Services.SPADES ),
    UserTargets.SPECIES:        Checkpoints.SPECIES,
    UserTargets.REFERENCE:      Checkpoints.REFERENCE,
    UserTargets.MLST:           ONE( Services.MLSTFINDER, Services.KCST ),
    UserTargets.RESISTANCE:     ALL( OPT( Services.RESFINDER ), OPT( Services.POINTFINDER ) ),
    UserTargets.VIRULENCE:      Services.VIRULENCEFINDER,
    UserTargets.PLASMIDS:       SEQ( Services.PLASMIDFINDER, Services.PMLSTFINDER ),
    UserTargets.PMLST:	        SEQ( Checkpoints.PLASMIDS, Services.PMLSTFINDER ),
    UserTargets.CGMLST:         Services.CGMLSTFINDER,
    UserTargets.SPECIALISED:    OPT( Services.CHOLERAEFINDER ),
    UserTargets.ANNOTATION:     Services.PROKKA,
    # The DEFAULT target depends on a list of standard targets.
    # All are optional so the pipeline runs till the end even if one fails.
    UserTargets.DEFAULT:        ALL( OPT(UserTargets.METRICS), OPT(UserTargets.SPECIES),
                                     OPT(UserTargets.MLST), OPT(UserTargets.RESISTANCE),
                                     OPT(UserTargets.VIRULENCE), OPT(UserTargets.PLASMIDS) ),
    UserTargets.FULL:           ALL( UserTargets.DEFAULT, OPT(UserTargets.ASSEMBLY), 
                                     OPT(UserTargets.CGMLST), OPT(UserTargets.SPECIALISED) ),

    Services.READSMETRICS:      OIF( Params.READS ),
    Services.QUAST:             ALL( OIF( Checkpoints.CONTIGS ), OPT( Checkpoints.REFERENCE ) ),
    Services.SKESA:             ALL( Params.ILLUMINA, Params.READS ),
    Services.SPADES:            ONE( Params.READS, ALL( Params.READS, Params.CONTIGS ) ),
    Services.KMERFINDER:        ONE( Params.READS, Checkpoints.CONTIGS ),
    Services.GETREFERENCE:      Services.KMERFINDER,  # Later: also work if species given and no KmerFinder
    Services.MLSTFINDER:        ALL( Checkpoints.SPECIES, ONE( Params.READS, Checkpoints.CONTIGS ) ),
    Services.KCST:              Checkpoints.CONTIGS,
    Services.RESFINDER:         ONE( Params.READS, Checkpoints.CONTIGS ),
    Services.POINTFINDER:       ALL( Checkpoints.SPECIES, ONE( Params.READS, Checkpoints.CONTIGS ) ),
    Services.VIRULENCEFINDER:   ALL( OPT( UserTargets.SPECIES ), ONE( Params.READS, Checkpoints.CONTIGS ) ),
    Services.PLASMIDFINDER:     ONE( Params.READS, Checkpoints.CONTIGS ),
    Services.PMLSTFINDER:       ALL( Checkpoints.PLASMIDS, ONE( Params.READS, Checkpoints.CONTIGS ) ),
    Services.CGMLSTFINDER:      ALL( Checkpoints.SPECIES, ONE( Params.READS, Checkpoints.CONTIGS ) ),
    Services.CHOLERAEFINDER:    ALL( Checkpoints.SPECIES, ONE( Params.READS, Checkpoints.CONTIGS ) ),
    Services.PROKKA:            ALL( Checkpoints.SPECIES, Checkpoints.CONTIGS, Checkpoints.REFERENCE ),

    Checkpoints.CONTIGS:        ONE( Params.CONTIGS, Services.SKESA, Services.SPADES ),
    Checkpoints.SPECIES:        ONE( Params.SPECIES, Services.KMERFINDER, Services.KCST ),
    Checkpoints.REFERENCE:      ONE( Params.REFERENCE, Services.GETREFERENCE ),
    Checkpoints.PLASMIDS:       ONE( Params.PLASMIDS, Services.PLASMIDFINDER ),
}    

# Consistency check on the DEPENDENCIES definitions

for v in Params:
    assert DEPENDENCIES.get(v) is None, "Params cannot have dependencies: %s" % v

for t in [ Checkpoints, Services, UserTargets ]:
    for v in t:
        assert DEPENDENCIES.get(v), "No dependency is defined for %s" % v


### Main 
#
#   The main() entry point for 'dry testing' the workflow defined above.
#
#   Invoke this module to get a CLI which 'executes' the workflow without running
#   any backend services.  You can query its runnable services, tell it which have
#   started, completed, or failed, and it will recompute the state, until the
#   workflow as a whole is fulfilled.

if __name__ == '__main__':

    import sys, argparse, functools, operator
    from pico.workflow.logic import Workflow

    def UserTargetOrService(s):
        '''Translate string to either a UserTarget or Service, throw if neither'''
        try: return UserTargets(s)
        except: return Services(s)

    # Parse arguments
    parser = argparse.ArgumentParser(description='''WorkflowLogic Tester''')
    parser.add_argument('-l', '--list', action='store_true', help="list the available params, services, and targets")
    parser.add_argument('-p', '--param', metavar='PARAM', action='append', default=[], help="set PARAM (option may repeat)")
    parser.add_argument('-x', '--exclude', metavar='SVC_OR_TGT', action='append', default=[], help="exclude service or user target (option may repeat)")
    parser.add_argument('-v', '--verbose', action='store_true', help="be more chatty")
    parser.add_argument('targets', metavar='TARGET', nargs='*', default=['DEFAULT'], help="User targets to complete")
    args = parser.parse_args()

    # Functional shorthands for the arg processing
    list_map = lambda f,i: list(map(f,i))
    list_concat = lambda ls : functools.reduce(operator.concat, ls, list())
    comma_split = lambda s: list(map(lambda i: i.strip(), s.split(',')))

    # Parse command-line options into lists of enum values of the proper type,
    # and pass to the Workflow constructor.
    # Note that strings can be converted to Enum using the Enum constructor.
    # We take into account that user may use comma-separated strings and/or repeat
    # options, so we deal with args that may look like: ['resistance', 'mlst,kcst'].
    try:
        w = Workflow(
            DEPENDENCIES,
            list_map(Params, list_concat(list_map(comma_split, args.param))),
            list_map(UserTargets, list_concat(list_map(comma_split, args.targets))),
            list_map(UserTargetOrService, list_concat(list_map(comma_split, args.exclude)))
            )
    except ValueError as e:
        print("Error: you specified an invalid target name: %s" % e, file=sys.stderr)
        sys.exit(1)

    # Handle the --list option by dumping all available params, targets, services
    if args.list:
        print('Params  : %s' % ', '.join(list_map(lambda x: x.value, Params)))
        print('Targets : %s' % ', '.join(list_map(lambda x: x.value, UserTargets)))
        print('Services: %s' % ', '.join(list_map(lambda x: x.value, Services)))
        sys.exit(0)

    # Check that we haven't failed or completed immediately
    if w.status == Workflow.Status.FAILED:
        print('The workflow failed immediately; did you forget to specify params?')
        sys.exit(0)
    elif w.status == Workflow.Status.COMPLETED:
        print('The workflow completed immediately; did you forget to specify targets?')
        sys.exit(0)

    # Print welcome header and prompt
    print('Workflow ready to rock; %d services are runnable (type \'r\' to see).' % len(w.list_runnable()))
    print('? ', end='', flush=True)

    # Iterate until user stops or workflow completes
    for line in sys.stdin:

        # Define a prompt that shows summary of current status
        prompt = lambda: print('\n[ %s | Runnable:%d Started:%d Completed:%d Failed:%d ] ? ' % (
            w.status.value, 
            len(w.list_runnable()), len(w.list_started()), len(w.list_completed()), len(w.list_failed())), 
            end='', flush=True)

        # Parse the input line into cmd and optional svc
        tok = list(map(lambda i: i.strip(), line.split(' ')))
        cmd = tok[0]
        try:
            svc = Services(tok[1]) if len(tok) > 1 else None
        except ValueError:
            print("Not a valid service name: %s" % tok[1])
            prompt()
            continue
 
        # Pretty print a list of enums as comma-sep values
        pprint = lambda l: print(', '.join(map(lambda s: s.value, l)))

        # Handle the commands
        if cmd.startswith('r'):
            pprint(w.list_runnable())
        elif cmd.startswith('s'):
            if svc:
                w.mark_started(svc)
            pprint(w.list_started())
        elif cmd.startswith('c'):
            if svc:
                w.mark_completed(svc)
            pprint(w.list_completed())
        elif cmd.startswith('f'):
            if svc:
                w.mark_failed(svc)
            pprint(w.list_failed())
        elif line.startswith("q"):
            break
        else:
            print("Commands (may be abbreviated): runnable, started [SVC], completed [SVC], failed [SVC], quit")

        # Else prompt for the next command
        prompt()

    # Done
    print('\nWorkflow status: %s' % w.status)
    if w.list_completed():
        print('- Completed : ', ', '.join(map(lambda s: s.value, w.list_completed())))
    if w.list_failed():
        print('- Failed    : ', ', '.join(map(lambda s: s.value, w.list_failed())))
    if w.list_started():
        print('- Started   : ', ', '.join(map(lambda s: s.value, w.list_started())))
    if w.list_runnable():
        print('- Runnable  : ', ', '.join(map(lambda s: s.value, w.list_runnable())))
    print()
