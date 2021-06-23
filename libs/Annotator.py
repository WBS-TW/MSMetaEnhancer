from libs.utils.Errors import ConversionNotSupported, DataNotRetrieved
from libs.services.CIR import CIR
from libs.services.CTS import CTS
from libs.services.NLM import NLM
from libs.services.PubChem import PubChem
from libs.utils.Job import convert_to_jobs


class Annotator:
    def __init__(self):
        self.services = {'CTS': CTS(), 'CIR': CIR(), 'NLM': NLM(), 'PubChem': PubChem()}

    def annotate(self, metadata, jobs, all=False, repeat=False):
        """
        Runs all jobs to add annotations to given dictionary containing metadata

        The method goes through specified jobs of form (Source, Target, Service)
        and tries to obtain 'Target' attribute based on 'Source' attribute using
        'Service' service.

        :param metadata: given spectra metadata
        :param jobs: specified list of jobs to be executed
        :param all: specifies if all possible jobs should be executed instead of given ones
        :param repeat: if some metadata was added, all jobs are executed again
        :return: annotated dictionary
        """
        if all:
            jobs = self.get_all_conversions()

        jobs = convert_to_jobs(jobs)

        added_metadata = True
        while added_metadata:
            added_metadata = False
            for job in jobs:
                service = self.services.get(job.service, None)
                data = metadata.get(job.source, None)

                if job.target in metadata:
                    pass  # TODO: log - data already present
                elif service is None:
                    pass  # TODO: log - unknown service
                elif data is None:
                    pass  # TODO: log - source data not available for conversion
                else:
                    try:
                        result = service.convert(job.source, job.target, data)
                        metadata[job.target] = result
                        if repeat:
                            added_metadata = True
                    except ConversionNotSupported:
                        pass  # TODO log this type of conversion is not supported by the service
                    except DataNotRetrieved:
                        pass  # TODO log no data were retrieved
        return metadata

    def get_all_conversions(self):
        """
        Method to compute all available conversion functions of all available Services.

        Assumes that the functions always have from {source}_to_{target}

        :return: a list of available conversion functions
        """
        jobs = []
        for service in self.services:
            methods = [method_name for method_name in dir(self.services[service]) if '_to_' in method_name]
            for method in methods:
                jobs.append((*method.split('_to_'), service))
        return jobs
