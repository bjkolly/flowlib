# -*- coding: utf-8 -*-
import copy
import io
import os
import re
import sys
import shutil
import json
import yaml

import flowlib.parser
import flowlib.nifi.rest
import flowlib.nifi.docs
from flowlib.exceptions import FlowLibException
from flowlib.model.flow import Flow
from flowlib.model.deployment import FlowDeployment
from flowlib.logger import log


def gen_flow_scaffold(dest):
    """
    :param dest: The destination directory to create a new flowlib project scaffold
    :type dest: str
    """
    if os.path.exists(dest):
        raise FlowLibException("Destination directory already exists {}".format(dest))

    log.info("Generating Flowlib project scaffold at {}".format(dest))
    init_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'init'))
    shutil.copytree(init_dir, dest)


def gen_flowlib_docs(config, dest):
    """
    Use the configured NiFi api endpoint to generate html docs containing example YAML definitions for the available
      processors, controller service, and reporting tasks
    :type config: FlowLibConfig
    :param dest: The destination directory to create the flowlib documentation
    :type dest: str
    """
    log.info("Generating Flowlib documentation for {} at {}".format(config.nifi_endpoint, dest))
    try:
        flowlib.nifi.docs.generate_docs(config, dest, config.force)
    except FlowLibException as e:
        log.error(e)
        raise


def new_flow_from_deployment(deployment_json, validate=True):
    """
    Construct a new flow from a deployment json file.
    :param deployment_json: The flow deployment as a json file
    :type deployment_json: io.TextIOWrapper
    :raises: FlowLibException
    """
    deployment = FlowDeployment.from_dict(json.load(deployment_json))
    flow = Flow(copy.deepcopy(deployment.flow), **deployment.flow)
    flow.flowlib_version = flowlib.__version__
    flow.initialize(with_components=deployment.components)
    if validate:
        flow.validate()
    return flow


def new_flow_from_yaml(flow_yaml, component_dir=None, validate=True):
    """
    Construct a new flow from a yaml file
    :param flow_yaml: The flow defined as a yaml file
    :type flow_yaml: io.TextIOWrapper
    :param component_dir: The directory of re-useable flow components
    :type component_dir: str
    :raises: FlowLibException
    """
    raw = yaml.safe_load(flow_yaml)

    # If --component-dir is specified, use that.
    # Otherwise use the components/ directory relative to flow.yaml
    if component_dir:
        component_dir = os.path.abspath(component_dir)
    else:
        component_dir = os.path.abspath(os.path.join(os.path.dirname(flow_yaml.name), 'components'))

    flow = Flow(copy.deepcopy(raw), **raw)
    flow.flowlib_version = flowlib.__version__
    flow.initialize(component_dir=component_dir)
    if validate:
        flow.validate()
    return flow


def validate_flow(config):
    """
    :type config: FlowLibConfig
    """
    log.info("Validating NiFi Flow YAML {}".format(config.flow_yaml))
    try:
        with open(config.flow_yaml, 'r') as f:
            new_flow_from_yaml(f, config.component_dir)
    except FlowLibException as e:
        log.error(e)
        raise


def deploy_flow(config):
    """
    :type config: FlowLibConfig
    """
    log.info("Deploying NiFi flow to {}".format(config.nifi_endpoint))
    try:
        with open(config.flow_yaml, 'r') as f:
            flow = new_flow_from_yaml(f, config.component_dir)

        flowlib.nifi.rest.deploy_flow(flow, config, force=config.force)
        log.info("Flow deployment completed successfully")
    except FlowLibException as e:
        log.error("Flow deployment failed")
        log.error(e)
        raise


def export_flow(config):
    """
    :type config: FlowLibConfig
    :return: io.TextIOWrapper
    """
    log.info("Exporting NiFi flow deployment {} from {}".format(config.export, config.nifi_endpoint))
    try:
        deployment = flowlib.nifi.rest.get_deployed_flow(config.nifi_endpoint, config.export)
        s = io.StringIO()
        deployment.save(s)
        return s
    except FlowLibException as e:
        log.error(e)
        raise


def configure_flow_controller(config):
    """
    :type config: FlowLibConfig
    """
    log.info("Configuring Flow Controller for {}".format(config.nifi_endpoint))
    try:
        flowlib.nifi.rest.configure_flow_controller(config.nifi_endpoint, config.reporting_task_controllers,
            config.reporting_tasks, config.max_timer_driven_threads, config.max_event_driven_threads, config.force)
        log.info("Flow Controller configuration completed successfully")
    except FlowLibException as e:
        log.error("Flow Controller configuration failed")
        log.error(e)
        raise


def list_components(config, component_type):
    """
    :type config: FlowLibConfig
    :param component_type: List the available components for this type
    :type component_type: str
    :return: list(str)
    """
    log.debug("Listing all available {}...".format(component_type))
    try:
        return flowlib.nifi.docs.list_components(config.docs_directory, component_type)
    except FlowLibException as e:
        log.error(e)
        raise


def describe_component(config, component_type, package_id):
    """
    :type config: FlowLibConfig
    :param component_type: The type of component being described
    :type component_type: str
    :param package_id: The package id of the component to describe
    :type package_id: str
    :return: dict(str:dict(PropertyDescriptorDTO))
    """
    log.debug("Describing {}: {}...".format(component_type, package_id))
    try:
        return flowlib.nifi.docs.describe_component(config.docs_directory, component_type, package_id)
    except FlowLibException as e:
        log.error(e)
        raise
