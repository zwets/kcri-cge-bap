#!/usr/bin/env python3
#
# kcri.bap.shims.GetReference - service shim to the GetReference backend
#

import os, logging
from pico.workflow.executor import Execution
from pico.jobcontrol.job import JobSpec, Job
from .base import BAPServiceExecution, UserException
from .KmerFinder import find_db as find_kmer_db
from .versions import BACKEND_VERSIONS

# Our service name and current backend version
SERVICE, VERSION = "GetReference", BACKEND_VERSIONS['odds-and-ends']

# Backend resource parameters: cpu, memory, disk, run time reqs
MAX_CPU = 1
MAX_MEM = 1
MAX_SPC = 1
MAX_TIM = 1 * 60

# The Service class
class GetReferenceShim:
    '''Service shim that executes the backend.'''

    def execute(self, ident, blackboard, scheduler):
        '''Invoked by the executor.  Creates, starts and returns the Execution.'''

        execution = GetReferenceExecution(SERVICE, VERSION, ident, blackboard, scheduler)

        # Get the execution parameters from the blackboard
        try:
            # Retrieve the accession
            closest = execution.get_closest_reference()
            accession = closest.get('accession')
            if not accession:
                raise UserException('no closest reference was found')

            # Retrieve the KMA database to retrieve it from
            kf_dbroot = execution.get_db_path('kmerfinder')
            kf_search = execution.get_user_input('kf_s')
            kma_db, _tax = find_kmer_db(kf_dbroot, kf_search)

            # Write to accession.fna (assuming it has no weird chars)
            out_file = accession + '.fna'

            params = [ 
                '--out-file', out_file,
                kma_db,
                accession
            ]

            job_spec = JobSpec('kma-retrieve', params, MAX_CPU, MAX_MEM, MAX_SPC, MAX_TIM)
            execution.store_job_spec(job_spec.as_dict())
            execution.start(job_spec, out_file)

        # Failing inputs will throw UserException
        except UserException as e:
            execution.fail(str(e))

        # Deeper errors additionally dump stack
        except Exception as e:
            logging.exception(e)
            execution.fail(str(e))

        return execution

# Single execution of the service
class GetReferenceExecution(BAPServiceExecution):
    '''A single execution of the service.'''

    _job = None
    _out_file = None

    def start(self, job_spec, out_file):
        if self.state == Execution.State.STARTED:
            self._out_file = out_file
            self._job = self._scheduler.schedule_job('retrieve-ref', job_spec, 'Reference')

    def collect_output(self, job):

        path = job.file_path(self._out_file)

        if os.path.isfile(path):
            self.store_results({ 'fasta_file': path })
            self._blackboard.put_closest_reference_path(path)
        else:
            self.fail("backend job produced no output, check: %s", job.file_path(""))
