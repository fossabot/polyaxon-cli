# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import uuid

import click
import sys

from polyaxon_client.exceptions import PolyaxonHTTPError, PolyaxonShouldExitError
from polyaxon_schemas.experiment import ExperimentConfig
from polyaxon_schemas.project import ExperimentGroupConfig

from polyaxon_cli.cli.check import check_polyaxonfile
from polyaxon_cli.cli.project import get_current_project_or_exit
from polyaxon_cli.utils.clients import PolyaxonClients
from polyaxon_cli.utils.formatting import Printer, dict_tabulate


@click.command()
@click.option('--file', '-f', multiple=True, type=click.Path(exists=True),
              help='The polyaxon files to run.')
@click.option('--description', type=str,
              help='The description to give to this run.')
def run(file, description):
    """Command for running polyaxonfile specification.

    Example:

    ```
    polyaxon run -f file -f file_override ...
    ```
    """
    file = file or 'polyaxonfile.yml'
    plx_file = check_polyaxonfile(file)
    num_experiments, concurrency = plx_file.experiments_def
    project = get_current_project_or_exit()
    project_client = PolyaxonClients().project
    if num_experiments == 1:
        click.echo('Creating an independent experiment.')
        experiment = ExperimentConfig(description=description,
                                      content=plx_file._data,
                                      config=plx_file.experiment_specs[0].parsed_data)
        try:
            response = project_client.create_experiment(project.user,
                                                        project.name,
                                                        experiment)
        except (PolyaxonHTTPError, PolyaxonShouldExitError) as e:
            Printer.print_error('Could not create experiment.')
            Printer.print_error('Error message `{}`.'.format(e))
            sys.exit(1)
        Printer.print_success('Experiment was created')
    else:
        click.echo('Creating an experiment group with {} experiments.'.format(num_experiments))
        experiment_group = ExperimentGroupConfig(description=description,
                                                 content=plx_file._data)
        try:
            response = project_client.create_experiment_group(project.user,
                                                              project.name,
                                                              experiment_group)
            Printer.print_success('Experiment group was created')
        except (PolyaxonHTTPError, PolyaxonShouldExitError) as e:
            Printer.print_error('Could not create experiment group.')
            Printer.print_error('Error message `{}`.'.format(e))
            sys.exit(1)
    response = response.to_dict()
    dict_tabulate(response)
