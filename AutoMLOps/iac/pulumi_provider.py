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

"""Builds Pulumi Files"""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=unused-import

from AutoMLOps.utils.utils import (
    write_file,
    make_dirs,
)

from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    RIGHT_BRACKET,
    LEFT_BRACKET,
    NEWLINE,
)

from AutoMLOps.iac.enums import PulumiRuntime
from AutoMLOps.iac.configs import PulumiConfig


def builder(
    project_id: str,
    config: PulumiConfig,
):
    """Constructs and writes pulumi scripts: Generates infrastructure using pulumi resource management style.

    Args:
        project_id: The project ID.
        provider: The provider option (default: Provider.TERRAFORM).
        config.pipeline_model_name: Name of the model being deployed.
        config.region: region used in gcs infrastructure config.
        config.gcs_bucket_name: gcs bucket name to use as part of the model infrastructure.
        config.artifact_repo_name: name of the artifact registry for the model infrastructure.
        config.source_repo_name: source repository used as part of the the model infra.
        config.cloudtasks_queue_name: name of the task queue used for model scheduling.
        config.cloud_build_trigger_name: name of the cloud build trigger for the model infra.
        config.pulumi_runtime: The pulumi runtime option (default: PulumiRuntime.PYTHON).
    """

    # Define the model name for the IaC configurations
    # remove special characters and spaces
    pipeline_model_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.pipeline_model_name]).lower()

    gcs_bucket_name = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in config.gcs_bucket_name]).lower()

    artifact_repo_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.artifact_repo_name]).lower()

    source_repo_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.source_repo_name]).lower()

    cloudtasks_queue_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.cloudtasks_queue_name]).lower()

    cloud_build_trigger_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.cloud_build_trigger_name]).lower()

    # create pulumi folder
    make_dirs([pipeline_model_name + '/'])
    pulumi_folder = pipeline_model_name + '/'

    # create Pulumi.yaml
    write_file(pulumi_folder + 'Pulumi.yaml', _create_pulumi_yaml(
        pipeline_model_name=pipeline_model_name,
        pulumi_runtime=config.pulumi_runtime), 'w+')

    # create Pulumi.dev.yaml
    write_file(pulumi_folder + 'Pulumi.dev.yaml', _create_pulumi_dev_yaml(
        project_id=project_id,
        pipeline_model_name=pipeline_model_name,
        region=config.region,
        gcs_bucket_name=gcs_bucket_name), 'w+')

    # create __main__.py
    if config.pulumi_runtime == PulumiRuntime.PYTHON:
        write_file(pulumi_folder + '__main__.py', _create_main_python(
            artifact_repo_name=artifact_repo_name,
            source_repo_name=source_repo_name,
            cloudtasks_queue_name=cloudtasks_queue_name,
            cloud_build_trigger_name=cloud_build_trigger_name), 'w+')


def _create_pulumi_yaml(
        pipeline_model_name: str,
        pulumi_runtime: str,
) -> str:
    """Generates code for Pulumi.yaml, the pulumi script that contains details to deploy project's GCP environment.

    Args:
        config.pipeline_model_name: Name of the model being deployed.
        config.pulumi_runtime: The pulumi runtime option (default: PulumiRuntime.PYTHON).

    Returns:
        str: Pulumi.yaml config script.
    """

    return (
        GENERATED_LICENSE +
        f'name: devops_plm_automlops_{pipeline_model_name}{NEWLINE}'
        f'runtime:{NEWLINE}'
        f'  name: {pulumi_runtime.value}{NEWLINE}'
        f'description: Pulumi stack generated by AutoMLOps for "{pipeline_model_name}" model{NEWLINE}'
    )


def _create_pulumi_dev_yaml(
        project_id: str,
        pipeline_model_name: str,
        region: str,
        gcs_bucket_name: str,
) -> str:
    """Generates code for Pulumi.dev.yaml, the pulumi script that contains details to deploy dev environment config.

    Args:
        project_id: The project ID.
        config.pipeline_model_name: Name of the model being deployed.
        config.region: region used in gcs infrastructure config.
        config.gcs_bucket_name: gcs bucket name to use as part of the model infrastructure.

    Returns:
        str: Pulumi.dev.yaml config script.
    """

    return (
        GENERATED_LICENSE +
        f'config:{NEWLINE}'
        f'  devops_plm_automlops_{pipeline_model_name}:general:{NEWLINE}'
        f'    project_id: {project_id}{NEWLINE}'
        f'    model_name: {pipeline_model_name}{NEWLINE}'
        f'    environment: dev{NEWLINE}'
        f'    default_region: {region}{NEWLINE}'
        f'  devops_plm_automlops_{pipeline_model_name}:buckets:{NEWLINE}'
        f'    - name: {gcs_bucket_name}{NEWLINE}'
        f'      location: {region}{NEWLINE}'
        f'      labels:{NEWLINE}'
        f'        provider: {pipeline_model_name}{NEWLINE}'
        f'  devops_plm_automlops_{pipeline_model_name}:service_accounts:{NEWLINE}'
        f'    - account_id: pipeline-runner-sa{NEWLINE}'
        f'      description: For submitting PipelineJobs{NEWLINE}'
        f'      display_name: Pipeline Runner Service Account{NEWLINE}'
        f'    - account_id: cloudbuild-runner-sa{NEWLINE}'
        f'      description: For submitting Cloud Build Jobs{NEWLINE}'
        f'      display_name: Cloud Build Runner Service Account{NEWLINE}'
        f'  devops_plm_automlops_{pipeline_model_name}:service_accounts_iam:{NEWLINE}'
        f'    - name: pipeline-runner-sa{NEWLINE}'
        f'      account_id: serviceAccount:pipeline-runner-sa@{project_id}.iam.gserviceaccount.com{NEWLINE}'
        f'      description: IAM roles for submitting PipelineJobs{NEWLINE}'
        f'      role_bindings:{NEWLINE}'
        f'        - roles/aiplatform.user{NEWLINE}'
        f'        - roles/artifactregistry.reader{NEWLINE}'
        f'        - roles/bigquery.user{NEWLINE}'
        f'        - roles/bigquery.dataEditor{NEWLINE}'
        f'        - roles/iam.serviceAccountUser{NEWLINE}'
        f'        - roles/storage.admin{NEWLINE}'
        f'        - roles/run.admin{NEWLINE}'
        f'    - name: cloudbuild-runner-sa{NEWLINE}'
        f'      account_id: serviceAccount:cloudbuild-runner-sa@{project_id}.iam.gserviceaccount.com{NEWLINE}'
        f'      description: IAM roles for submitting Cloud Build Jobs{NEWLINE}'
        f'      role_bindings:{NEWLINE}'
        f'        - roles/run.admin{NEWLINE}'
        f'        - roles/iam.serviceAccountUser{NEWLINE}'
        f'        - roles/cloudtasks.enqueuer{NEWLINE}'
        f'        - roles/cloudscheduler.admin{NEWLINE}'
    )


def _create_main_python(
    artifact_repo_name,
    source_repo_name,
    cloudtasks_queue_name,
    cloud_build_trigger_name,
) -> str:
    """Generates code for __main__.py, the pulumi script that creates the primary resources.

    Args:
        artifact_repo_name: name of the artifact registry for the model infrastructure.
        source_repo_name: source repository used as part of the the model infra.
        cloudtasks_queue_name: name of the task queue used for model scheduling.
        cloud_build_trigger_name: name of the cloud build trigger for the model infra.

    Returns:
        str: Main pulumi script.
    """

    return (
        GENERATED_LICENSE +
        f'import os{NEWLINE}'
        f'import pulumi{NEWLINE}'
        f'import pulumi_gcp as gcp{NEWLINE}'
        f'from pulumi import Config, log, ResourceOptions, StackReference, export{NEWLINE}'
        f'{NEWLINE}'
        f'config = Config(){NEWLINE}'
        f'{NEWLINE}'
        f'#######################################################################################\n'
        f'# General Config{NEWLINE}'
        f'#######################################################################################\n'
        f'general_cfg = config.require_object("general"){NEWLINE}'
        f'project_id = general_cfg.get("project_id"){NEWLINE}'
        f'model_name = general_cfg.get("model_name"){NEWLINE}'
        f'environment = general_cfg.get("environment"){NEWLINE}'
        f'default_region = general_cfg.get("default_region"){NEWLINE}'
        f'{NEWLINE}'
        f'vertex_pipeline_name = f"{LEFT_BRACKET}model_name{RIGHT_BRACKET}"{NEWLINE}'
        f'\n'
        f'stack_infra = f"{LEFT_BRACKET}model_name{RIGHT_BRACKET}-{LEFT_BRACKET}environment{RIGHT_BRACKET}"{NEWLINE}'
        f'{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'# Service Accounts Config{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'service_accounts = config.require_object("service_accounts") or []{NEWLINE}'
        f'{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'# Storage Config{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'buckets = config.require_object("buckets") or []{NEWLINE}'
        f'{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'# IAMMember Bindings Config{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'iam_cfg = config.require_object("service_accounts_iam"){NEWLINE}'
        f'iam_cfg = list(iam_cfg) if iam_cfg else []{NEWLINE}'
        f'{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'# Init{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'try:{NEWLINE}'
        f'    if buckets:{NEWLINE}'
        f'        for i, bucket in enumerate(buckets):{NEWLINE}'
        f'            gcp.storage.Bucket({NEWLINE}'
        f'                resource_name=f\'{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{LEFT_BRACKET}bucket[\"name\"]{RIGHT_BRACKET}-{LEFT_BRACKET}i{RIGHT_BRACKET}\',{NEWLINE}'
        f'                project=project_id,{NEWLINE}'
        f'                name=bucket["name"],{NEWLINE}'
        f'                location=bucket["location"],{NEWLINE}'
        f'                labels=bucket["labels"],{NEWLINE}'
        f'                opts=ResourceOptions({NEWLINE}'
        f'                    depends_on=[]{NEWLINE}'
        f'                ){NEWLINE}'
        f'            ){NEWLINE}'
        f'{NEWLINE}'
        f'    if service_accounts:{NEWLINE}'
        f'        for i, svc in enumerate(service_accounts):{NEWLINE}'
        f'            gcp.serviceaccount.Account({NEWLINE}'
        f'                resource_name=f\'{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{LEFT_BRACKET}svc[\"account_id\"]{RIGHT_BRACKET}-{LEFT_BRACKET}i{RIGHT_BRACKET}\',{NEWLINE}'
        f'                project=project_id,{NEWLINE}'
        f'                account_id=svc["account_id"],{NEWLINE}'
        f'                display_name=svc["display_name"],{NEWLINE}'
        f'                description=svc["description"],{NEWLINE}'
        f'                opts=ResourceOptions({NEWLINE}'
        f'                    depends_on=[]{NEWLINE}'
        f'                ){NEWLINE}'
        f'            ){NEWLINE}'
        f'{NEWLINE}'
        f'##################################################################################{NEWLINE}'
        f'## IAMMember - service_accounts_iam:{NEWLINE}'
        f'##################################################################################{NEWLINE}'
        f'    for iam_obj in iam_cfg:{NEWLINE}'
        f'        for iam_role in iam_obj[\"role_bindings\"]:{NEWLINE}'
        f'            gcp.projects.IAMMember({NEWLINE}'
        f'                resource_name=f\'{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{LEFT_BRACKET}iam_obj[\"name\"]{RIGHT_BRACKET}-{LEFT_BRACKET}iam_obj[\"role_bindings\"].index(iam_role){RIGHT_BRACKET}\',{NEWLINE}'
        f'                member=iam_obj[\"account_id\"],{NEWLINE}'
        f'                project=project_id,{NEWLINE}'
        f'                role=iam_role,{NEWLINE}'
        f'                opts=ResourceOptions({NEWLINE}'
        f'                    depends_on=[{NEWLINE}'
        f'                    ]{NEWLINE}'
        f'                ),{NEWLINE}'
        f'            ){NEWLINE}'
        f'{NEWLINE}'
        f'    artifactregistry_repo = gcp.artifactregistry.Repository({NEWLINE}'
        f'        resource_name=f\"{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{artifact_repo_name}\",{NEWLINE}'
        f'        project=project_id,{NEWLINE}'
        f'        description=\"Docker artifact repository\",{NEWLINE}'
        f'        format="DOCKER",{NEWLINE}'
        f'        location=default_region,{NEWLINE}'
        f'        repository_id=\"{artifact_repo_name}\",{NEWLINE}'
        f'        opts=ResourceOptions({NEWLINE}'
        f'            depends_on=[]{NEWLINE}'
        f'        ){NEWLINE}'
        f'    ){NEWLINE}'
        f'{NEWLINE}'
        f'    source_repo = gcp.sourcerepo.Repository({NEWLINE}'
        f'        resource_name=f\"{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{source_repo_name}\",{NEWLINE}'
        f'        name=\"{source_repo_name}\",{NEWLINE}'
        f'        project=project_id,{NEWLINE}'
        f'        opts=ResourceOptions({NEWLINE}'
        f'            depends_on=[]{NEWLINE}'
        f'        ){NEWLINE}'
        f'    ){NEWLINE}'
        f'{NEWLINE}'
        f'    cloudtasks_queue = gcp.cloudtasks.Queue({NEWLINE}'
        f'        resource_name=f\"{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{cloudtasks_queue_name}\",{NEWLINE}'
        f'        name=\"{cloudtasks_queue_name}\",{NEWLINE}'
        f'        project=project_id,{NEWLINE}'
        f'        location=default_region,{NEWLINE}'
        f'        opts=ResourceOptions({NEWLINE}'
        f'            depends_on=[]{NEWLINE}'
        f'        ){NEWLINE}'
        f'    ){NEWLINE}'
        f'{NEWLINE}'
        f'    cloudbuild_trigger = gcp.cloudbuild.Trigger({NEWLINE}'
        f'        resource_name=f\"{LEFT_BRACKET}stack_infra{RIGHT_BRACKET}-{cloud_build_trigger_name}\",{NEWLINE}'
        f'        name=\"{cloud_build_trigger_name}\",{NEWLINE}'
        f'        project=project_id,{NEWLINE}'
        f'        filename=\"cloudbuild.yaml\",{NEWLINE}'
        f'        service_account=f\"projects/{LEFT_BRACKET}project_id{RIGHT_BRACKET}/serviceAccounts/cloudbuild-runner-sa@{LEFT_BRACKET}project_id{RIGHT_BRACKET}.iam.gserviceaccount.com\",{NEWLINE}'
        f'        location=default_region,{NEWLINE}'
        f'        trigger_template=gcp.cloudbuild.TriggerTriggerTemplateArgs({NEWLINE}'
        f'            branch_name=\"main\",{NEWLINE}'
        f'            repo_name=\"{source_repo_name}\",{NEWLINE}'
        f'        ),{NEWLINE}'
        f'        opts=ResourceOptions({NEWLINE}'
        f'            depends_on=[{NEWLINE}'
        f'                source_repo{NEWLINE}'
        f'            ]{NEWLINE}'
        f'        ){NEWLINE}'
        f'    ){NEWLINE}'
        f'{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
        f'except Exception as ex:{NEWLINE}'
        f'    log.error(f\"Environment {LEFT_BRACKET}environment{RIGHT_BRACKET} -> {LEFT_BRACKET}ex{RIGHT_BRACKET}\"){NEWLINE}'
        f'    raise ex{NEWLINE}'
        f'#######################################################################################{NEWLINE}'
    )
