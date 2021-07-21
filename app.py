import asyncio
import aiohttp

from libs.Annotator import Annotator
from libs.Curator import Curator
from libs.Spectra import Spectra
from libs.utils import logger
from libs.utils.Errors import UnknownService, UnknownSpectraFormat
from libs.utils.Job import convert_to_jobs
from libs.services import *


class Application:
    def __init__(self, log_level='warning', log_file=None):
        self.log_level = log_level
        self.log_file = log_file
        self.spectra = Spectra()

    @staticmethod
    def validate_services(services):
        """
        Check if services do exist.
        Raises UnknownService if a service does not exist.

        :param services: given list of services names
        """
        for service in services:
            try:
                eval(service)
            except NameError:
                raise UnknownService(f'Service {service} unknown.')

    def load_spectra(self, filename, file_format):
        """
        High level method to load Spectra data from given file.

        :param filename: path to source spectra file
        :param file_format: format of spectra
        """
        try:
            getattr(self.spectra, f'load_from_{file_format}')(filename)
        except Exception:
            raise UnknownSpectraFormat(f'Format {file_format} not supported.')

    def save_spectra(self, filename, file_format):
        """
        High level method to save Spectra data to given file.

        :param filename: path to target file
        :param file_format: desired format of spectra
        """
        try:
            getattr(self.spectra, f'save_to_{file_format}')(filename)
        except Exception:
            raise UnknownSpectraFormat(f'Format {file_format} not supported.')

    def curate_spectra(self):
        """
        Updates current Spectra data by curation process.
        """
        self.spectra = Curator().curate_spectra(self.spectra)

    async def annotate_spectra(self, services, jobs=None, batch_size=10, repeat=False):
        """
        Annotates current Spectra data by specified jobs.
         Used services must be specified.
         Jobs do not have to be given, all available jobs will be executed instead.

        :param services: given list of services names
        :param jobs: list specifying jobs to be executed
        :param batch_size: amount of data processed asynchronously at once
        :param repeat: if some metadata was added, all jobs are executed again
        """
        results = []
        async with aiohttp.ClientSession() as session:
            self.validate_services(services)
            services = {service: eval(service)(session) for service in services}
            annotator = Annotator(services)

            # create all possible jobs if not given
            if not jobs:
                jobs = annotator.get_all_conversions()
            jobs = convert_to_jobs(jobs)

            logger.set_target_attributes(jobs)

            for size in range(len(self.spectra.spectrums) // batch_size + 1):
                results += await asyncio.gather(*[annotator.annotate(spectra, jobs, repeat) for spectra in
                                                  self.spectra.spectrums[size * batch_size:(size + 1) * batch_size]])

        self.spectra.spectrums = results
        logger.log_statistics(self.log_level, self.log_file)