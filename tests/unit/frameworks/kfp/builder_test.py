# Copyright 2023 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for kfp builder module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from AutoMLOps.frameworks.kfp.builder import (
    build,  # Does not necessarily need to be tested, a combination of other functions
    build_component,
    build_pipeline,
    build_cloudrun,  # Does not necessarily need to be tested, a combination of other functions
)
import mock
import os
import pytest
import AutoMLOps.utils.utils
from AutoMLOps.utils.utils import write_yaml_file, read_yaml_file, make_dirs

TEMP_YAML = {
    "name": "create_dataset",
    "description": "Custom component that takes in a BQ table and writes it to GCS.",
    "inputs": [
        {
            "name": "bq_table",
            "description": "The source biquery table.",
            "type": "String",
        },
        {
            "name": "data_path",
            "description": "The gcs location to write the csv.",
            "type": "String",
        },
        {"name": "project_id", "description": "The project ID.", "type": "String"},
    ],
    "implementation": {
        "container": {
            "image": "TBD",
            "command": [
                "sh",
                "-c",
                'if ! [ -x "$(command -v pip)" ]; then\n    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip\nfi\nPIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \\\n    --no-warn-script-location  && "$0" "$@"\n\n',
                'def create_dataset(\n    bq_table: str,\n    data_path: str,\n    project_id: str\n):\n    """Custom component that takes in a BQ table and writes it to GCS.\n\n    Args:\n        bq_table: The source biquery table.\n        data_path: The gcs location to write the csv.\n        project_id: The project ID.\n    """\n    from google.cloud import bigquery\n    import pandas as pd\n    from sklearn import preprocessing\n\n    bq_client = bigquery.Client(project=project_id)\n\n    def get_query(bq_input_table: str) -> str:\n        """Generates BQ Query to read data.\n\n        Args:\n        bq_input_table: The full name of the bq input table to be read into\n        the dataframe (e.g. <project>.<dataset>.<table>)\n        Returns: A BQ query string.\n        """\n        return f\'\'\'\n        SELECT *\n        FROM `{bq_input_table}`\n        \'\'\'\n\n    def load_bq_data(query: str, client: bigquery.Client) -> pd.DataFrame:\n        """Loads data from bq into a Pandas Dataframe for EDA.\n        Args:\n        query: BQ Query to generate data.\n        client: BQ Client used to execute query.\n        Returns:\n        pd.DataFrame: A dataframe with the requested data.\n        """\n        df = client.query(query).to_dataframe()\n        return df\n\n    dataframe = load_bq_data(get_query(bq_table), bq_client)\n    le = preprocessing.LabelEncoder()\n    dataframe[\'Class\'] = le.fit_transform(dataframe[\'Class\'])\n    dataframe.to_csv(data_path, index=False)\n',
            ],
            "args": [
                "--executor_input",
                {"executorInput": None},
                "--function_to_execute",
                "create_dataset",
            ],
        }
    },
}

@pytest.fixture(params=[TEMP_YAML])
def temp_yaml_dict(request, tmpdir):
    """Writes temporary yaml file fixture using defaults parameterized dictionaries
    during pytest session scope.

    Returns:
        dict: Path of yaml file and dictionary it contains.
    """
    yaml_path = tmpdir.join("test.yaml")
    write_yaml_file(yaml_path, request.param, "w")
    return {"path": yaml_path, "vals": request.param}

# Create defaults file contents to test
DEFAULTS = {
    'gcp':
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }

@pytest.fixture(params=[DEFAULTS])
def defaults_dict(request, tmpdir):
    """Writes temporary yaml file fixture using defaults parameterized dictionaries 
    during pytest session scope.

    Returns:
        dict: Path of yaml file and dictionary it contains.
    """

    yaml_path = tmpdir.join('defaults.yaml')
    write_yaml_file(yaml_path, request.param, 'w')

    return {'path': yaml_path, 'vals': request.param}

def test_build_component(mocker, tmpdir, temp_yaml_dict, defaults_dict):

    #Set up variable for the component name to use in assertions
    component_name = TEMP_YAML['name']

    #Patch filepath constants to point to test path.
    mocker.patch.object(AutoMLOps.frameworks.kfp.builder, 'GENERATED_DEFAULTS_FILE', defaults_dict['path'])
    mocker.patch.object(AutoMLOps.frameworks.kfp.builder, 'BASE_DIR', tmpdir)

    #create the required directories for build_component to use.
    make_dirs([f'{tmpdir}/random/component_base/src'])

    #call to build_component, passing in the constructed yaml
    build_component(temp_yaml_dict['path'])

    #assertions to ensure that correct files were created during build_component call
    assert os.path.exists(f'{tmpdir}/{component_name}/component.yaml')
    assert os.path.exists(f'{tmpdir}/components/component_base/src/{component_name}.py')
    assert os.path.exists(f'{tmpdir}/blah')

    #Load in the newly created component.yaml file and compare it to the expected output in test_data
    created_component_dict = read_yaml_file(f'{tmpdir}/components/{component_name}/component.yaml')
    expected_component_dict = read_yaml_file(f'{tmpdir}/component.yaml')
    assert created_component_dict == expected_component_dict

def test_build_pipeline():
    assert True