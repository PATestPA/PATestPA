import requests
import json
from datetime import datetime
import sys
import glob
import fnmatch
import os
import argparse
import time

import urllib.parse
import platform

from pathlib import Path  # User Home Folder references


class PackageAwareStructureAPIResponse:

    def __init__(self, structure_response):

        self.original_response = structure_response

        self.content_object = None

        self.structure_id = None
        self.project_id = None
        self.analysis_id = None
        self.report_url = None
        self.embed_url = None
        self.report_status_url = None

        if self.original_response is not None:

            self.content_object = json.loads(self.original_response.content)

            self.structure_id = self.content_object["Id"]
            self.project_id = self.content_object["projectId"]
            self.analysis_id = self.content_object["Id"]
            self.report_url = self.content_object["reportUrl"]
            self.embed_url = self.content_object["embedUrl"]
            self.report_status_url = self.content_object["reportStatusUrl"]


class PackageAwareStructureAPI:

    API_RETRY_COUNT = 3

    URI_TEMPLATE = "{pa_base_uri}clients/{pa_client_id}/analysis/structure"

    def __init__(self):
        pass

    @staticmethod
    def generate_api_url(pa_context):
        url = PackageAwareStructureAPI.URI_TEMPLATE
        url = url.replace("{pa_base_uri}", pa_context.base_uri)
        url = url.replace("{pa_client_id}", pa_context.client_id)

        return url

    @staticmethod
    def exec(pa_context):

        api_url = PackageAwareStructureAPI.generate_api_url(pa_context)

        api_response = None

        for i in range(0, PackageAwareStructureAPI.API_RETRY_COUNT):
            try:
                
                api_response = PackageAwareStructureAPIResponse(
                    requests.post(
                        url=api_url,
                        data=json.dumps({
                            "project": pa_context.project_name,
                            "name": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                        }),
                        headers={'x-pa-apikey': pa_context.api_key}
                    )
                )
                break

            except Exception as e:
                PackageAware.console_log("Structure API Exception Occurred. "
                      "Attempt " + str(i + 1) + " of " + str(PackageAwareStructureAPI.API_RETRY_COUNT))

        return api_response


class PackageAwareContext:

    def __init__(self):
        self.base_uri = None
        self.source_code_path = None
        self.project_name = None
        self.client_id = None
        self.api_key = None

    def reset(self):
        self.base_uri = None
        self.source_code_path = None
        self.project_name = None
        self.client_id = None
        self.api_key = None

    def load(self, args):

        # Prioritize context from environment variables
        # Any environment variables that are not set will
        # automatically be searched in the script arguments
        self.load_from_env_var()

        if not self.is_valid():

            # Attempt to get MISSING context from parameters
            self.load_from_parameters(args)

            if not self.is_valid():

                return False

        return True

    def load_from_env_var(self):

        self.reset()

        try:
            if self.base_uri is None:
                self.base_uri = os.environ["PACKAGE_AWARE_API_BASE_URI"]
                PackageAware.console_log("PACKAGE_AWARE_API_BASE_URI Environment Variable Loaded: " + self.base_uri)
        except Exception as e:
            pass

        try:
            if self.source_code_path is None:
                self.source_code_path = os.environ['PACKAGE_AWARE_ROOT_CODE_PATH']
                PackageAware.console_log("PACKAGE_AWARE_ROOT_CODE_PATH Environment Variable Loaded: " + self.source_code_path)
        except Exception as e:
            pass

        try:
            if self.project_name is None:
                self.project_name = os.environ['PACKAGE_AWARE_PROJECT_NAME']
                PackageAware.console_log("PACKAGE_AWARE_PROJECT_NAME Environment Variable Loaded: " + self.project_name)
        except Exception as e:
            pass

        try:
            if self.client_id is None:
                self.client_id = os.environ['PACKAGE_AWARE_CLIENT_ID']
                PackageAware.console_log("PACKAGE_AWARE_CLIENT_ID Environment Variable Loaded: SECRET")
        except Exception as e:
            pass

        try:
            if self.api_key is None:
                self.api_key = os.environ['PACKAGE_AWARE_API_KEY']
                PackageAware.console_log("PACKAGE_AWARE_API_KEY Environment Variable Loaded: SECRET")
        except Exception as e:
            pass

    def load_from_parameters(self, args):

        self.reset()

        if args.base_uri is not None:
            self.base_uri = str(args.base_uri)
            PackageAware.console_log("PACKAGE_AWARE_API_BASE_URI Parameter Loaded: " + self.base_uri)

        if args.source_code_path is not None:
            self.source_code_path = str(args.source_code_path)
            PackageAware.console_log("PACKAGE_AWARE_ROOT_CODE_PATH Parameter Loaded: " + self.source_code_path)

        if args.project_name is not None:
            self.project_name = str(args.project_name)
            PackageAware.console_log("PACKAGE_AWARE_PROJECT_NAME Parameter Loaded: " + self.project_name)

        if args.client_id is not None:
            self.client_id = str(args.client_id)
            PackageAware.console_log("PACKAGE_AWARE_CLIENT_ID Parameter Loaded: SECRET")

        if args.api_key is not None:
            self.api_key = str(args.api_key)
            PackageAware.console_log("PACKAGE_AWARE_API_KEY Parameter Loaded: SECRET")

    def is_valid(self):

        if self.base_uri is None or len(self.base_uri) == 0:
            return False

        if self.source_code_path is None or len(self.source_code_path) == 0:
            return False

        if self.project_name is None or len(self.project_name) == 0:
            return False

        if self.client_id is None or len(self.client_id) == 0:
            return False

        if self.api_key is None or len(self.api_key) == 0:
            return False

        return True

    def print_invalid(self):

        if self.base_uri is None or len(self.base_uri) == 0:
            PackageAware.console_log("REQUIRED PARAMETER IS MISSING: PACKAGE_AWARE_API_BASE_URI")

        if self.source_code_path is None or len(self.source_code_path) == 0:
            PackageAware.console_log("REQUIRED PARAMETER IS MISSING: PACKAGE_AWARE_ROOT_CODE_PATH")

        if self.project_name is None or len(self.project_name) == 0:
            PackageAware.console_log("REQUIRED PARAMETER IS MISSING: PACKAGE_AWARE_PROJECT_NAME")

        if self.client_id is None or len(self.client_id) == 0:
            PackageAware.console_log("REQUIRED PARAMETER IS MISSING: PACKAGE_AWARE_CLIENT_ID")
            PackageAware.console_log("CLIENT_ID, if you do not already have one, will be provided with a subscription to PackageAware.io services.")

        if self.api_key is None or len(self.api_key) == 0:
            PackageAware.console_log("REQUIRED PARAMETER IS MISSING: PACKAGE_AWARE_API_KEY")
            PackageAware.console_log("API_KEY, if you do not already have one, will be provided with a subscription to PackageAware.io services.")


class PackageAwareManifestAPI:

    API_RETRY_COUNT = 3

    URI_TEMPLATE = "{pa_base_uri}" \
                   "clients/{pa_client_id}" \
                   "/projects/{pa_project_id}" \
                   "/analysis/{pa_analysis_id}" \
                   "/manifests/{pa_manifest_name}"

    def __init__(self):
        pass

    @staticmethod
    def generate_api_url(pa_context, project_id, analysis_id, manifest_name):

        manifest_for_url = urllib.parse.quote(manifest_name)

        api_url = PackageAwareManifestAPI.URI_TEMPLATE
        api_url = api_url.replace("{pa_base_uri}", pa_context.base_uri)
        api_url = api_url.replace("{pa_client_id}", pa_context.client_id)
        api_url = api_url.replace("{pa_project_id}", project_id)
        api_url = api_url.replace("{pa_analysis_id}", analysis_id)
        api_url = api_url.replace("{pa_manifest_name}", manifest_for_url)

        return api_url

    @staticmethod
    def exec(pa_context, project_id, analysis_id, manifest_name, manifest_content):

        api_url = PackageAwareManifestAPI.generate_api_url(pa_context, project_id, analysis_id, manifest_name)

        response = None

        for i in range(0, PackageAwareManifestAPI.API_RETRY_COUNT):
            try:
                PackageAware.console_log("*** Putting manifest: " + manifest_name)

                response = requests.put(
                    url=api_url,
                    data=manifest_content,
                    headers={'x-pa-apikey': package_aware.context.api_key}
                )

                PackageAware.console_log("Manifest Put Executed: " + manifest_name)

                break

            except Exception as e:
                PackageAware.console_log("Manifest API Exception Occurred. "
                      "Attempt " + str(i + 1) + " of " + str(PackageAwareManifestAPI.API_RETRY_COUNT))

        return response


class PackageAware:

    MANIFEST_FILES = [
        {'file_pattern': 'Gemfile', 'package_manager': 'Ruby'},
        {'file_pattern': 'requirements.txt', 'package_manager': 'Python'},
        {'file_pattern': 'package.json', 'package_manager': 'NPM'},
        {'file_pattern': 'pom.xml', 'package_manager': 'Java'},
        {'file_pattern': 'pipfile', 'package_manager': 'Python'},
        {'file_pattern': 'Packages.config', 'package_manager': 'NuGet'},
        {'file_pattern': '*.csproj', 'package_manager': 'NuGet'}
    ]

    def __init__(self):
        self.context = PackageAwareContext()
        self.script = PackageAwareAnalysisScript()

    def find_manifest_files(self, file_pattern):
        return glob.glob(
            self.context.source_code_path + '/**/' + file_pattern,
            recursive=True
        )

    def send_manifests(self, project_id, analysis_id, dirs_to_exclude, files_to_exclude):

        manifests_found_count = 0

        code_root = PackageAware.get_current_directory()

        PackageAware.console_log("------------------------")
        PackageAware.console_log("Begin Recursive Manifest Search")
        PackageAware.console_log("------------------------")

        for manifest_file in PackageAware.MANIFEST_FILES:

            package_manager = manifest_file['package_manager']

            manifest_name = manifest_file['file_pattern']

            PackageAware.console_log("Looking for " + package_manager + " " + manifest_name + "...")

            files = self.find_manifest_files(manifest_file['file_pattern'])

            # iterate each
            # avoid directories to exclude
            for file_name in files:

                pure_filename = os.path.basename(file_name)
                pure_directory = os.path.dirname(file_name)

                if pure_directory.startswith("./"):
                    pure_directory = code_root + pure_directory[2:]
                elif pure_directory == ".":
                    pure_directory = code_root

                # Directories to Exclude
                if pure_directory in dirs_to_exclude:
                    # skip this manifest
                    PackageAware.console_log("Skipping file due to dirs_to_exclude: " + file_name)
                    continue

                # Files to Exclude
                full_file_path = pure_directory
                if full_file_path.find("/") >= 0:
                    if not full_file_path.endswith("/"):
                        full_file_path += "/" + pure_filename
                else:
                    if not full_file_path.endswith("\\"):
                        full_file_path += "\\" + pure_filename

                if full_file_path in files_to_exclude:
                    # skip this manifest
                    PackageAware.console_log("Skipping file due to files_to_exclude: " + file_name)
                    continue

                # log the manifest
                PackageAware.console_log("Found manifest file: " + file_name)

                # call the api with the manifest file content as the body

                try:

                    with open(file_name, 'r') as the_file:

                        content = the_file.read()

                        if len(content.strip()) > 0:

                            response = PackageAwareManifestAPI.exec(
                                pa_context=package_aware.context,
                                project_id=project_id,
                                analysis_id=analysis_id,
                                manifest_name=manifest_name,
                                manifest_content=content
                            )

                            PackageAware.console_log("Add manifest status code: " + str(response.status_code))

                            manifests_found_count += 1

                        else:
                            PackageAware.console_log("WARNING: Manifest file is empty: " + file_name)

                except Exception as e:
                    PackageAware.console_log("Could not send manifest: " + file_name + " due to error: " + str(e))

        return manifests_found_count

    @staticmethod
    def recursive_glob(treeroot, pattern):
        results = []
        for base, dirs, files in os.walk(treeroot):
            goodfiles = fnmatch.filter(files, pattern)
            results.extend(os.path.join(base, f) for f in goodfiles)
        return results

    @staticmethod
    def get_current_directory():
        current_folder = os.getcwd()
        plt = platform.system().lower()
        if plt != "windows":
            if current_folder[-1:] != "/":
                current_folder += "/"
        else:
            if current_folder[-1:] != "\\":
                current_folder += "\\"

        return current_folder

    @staticmethod
    def console_log(message):
        print(str(datetime.utcnow()) + " PACKAGE AWARE: " + message)

    def analysis_result_exec(self, report_status_url, analysis_result_max_wait, analysis_result_polling_interval):

        analysis_start_time = datetime.utcnow()

        while True:

            if (datetime.utcnow() - analysis_start_time).seconds > analysis_result_max_wait:
                PackageAware.console_log(
                    "Analysis Result Max Wait Time Reached (" + str(analysis_result_max_wait) + ")"
                )
                sys.exit(1)

            response = PackageAwareAnalysisResultAPI.exec(self.context, report_status_url)

            content_object = json.loads(response.content)

            if response.status_code == 200:

                analysis_status = str(content_object["status"])

                if analysis_status.lower() == "finished":
                    PackageAware.console_log("------------------------")
                    PackageAware.console_log("Analysis Completed Successfully")
                    PackageAware.console_log("------------------------")
                    sys.exit(0)
                elif analysis_status.lower().startswith("failed"):
                    PackageAware.console_log("------------------------")
                    PackageAware.console_log("Analysis complete - Failures reported.")

                    # Additional Messaging based on type of failure...
                    if analysis_status.lower().find("violation") >= 0:
                        PackageAware.console_log("FAILURE: Violations reported.")
                    elif analysis_status.lower().find("vulnerabilit") >= 0:
                        PackageAware.console_log("FAILURE: Vulnerabilities reported.")
                    else:
                        # Unknown failure - no additional messaging-out
                        pass
                    PackageAware.console_log("------------------------")

                    # Fail with error
                    sys.exit(1)

                elif analysis_status.lower() == "error":
                    PackageAware.console_log(
                        "Analysis Error. Will retry in " +
                        str(analysis_result_polling_interval) + " seconds."
                    )
                    time.sleep(analysis_result_polling_interval)
                    continue
                else:
                    # Status code that is not pertinent to the result
                    PackageAware.console_log(
                        "Analysis Ongoing. Will retry in " +
                        str(analysis_result_polling_interval) + " seconds."
                    )
                    time.sleep(analysis_result_polling_interval)
                    continue
            else:
                PackageAware.console_log("------------------------")
                PackageAware.console_log("ERROR: API Response Status Code: " + str(response.status_code))
                PackageAware.console_log("------------------------")
                sys.exit(1)


class PackageAwareAnalysisStartAPI:

    API_RETRY_COUNT = 3

    URI_TEMPLATE = "{pa_base_uri}clients/{pa_client_id}/projects/{pa_project_id}/analysis/{pa_analysis_id}"

    def __init__(self):
        pass

    @staticmethod
    def generate_api_url(pa_context, project_id, analysis_id):
        api_url = PackageAwareAnalysisStartAPI.URI_TEMPLATE
        api_url = api_url.replace("{pa_base_uri}", pa_context.base_uri)
        api_url = api_url.replace("{pa_client_id}", pa_context.client_id)
        api_url = api_url.replace("{pa_project_id}", project_id)
        api_url = api_url.replace("{pa_analysis_id}", analysis_id)

        return api_url

    @staticmethod
    def exec(pa_context, project_id, analysis_id):

        url = PackageAwareAnalysisStartAPI.generate_api_url(pa_context, project_id, analysis_id)

        response = None

        for i in range(0, PackageAwareAnalysisStartAPI.API_RETRY_COUNT):
            try:
                response = requests.put(
                    url=url,
                    data="{}",
                    headers={'x-pa-apikey': pa_context.api_key, 'content-length': str(0)}
                )

                break

            except Exception as e:
                PackageAware.console_log("Analysis Start API Exception Occurred. "
                      "Attempt " + str(i + 1) + " of " + str(PackageAwareAnalysisStartAPI.API_RETRY_COUNT))

        return response


class PackageAwareAnalysisResultAPI:

    API_RETRY_COUNT = 3

    def __init__(self):

        pass

    @staticmethod
    def exec(pa_context, result_uri):

        response = None

        for i in range(0, PackageAwareAnalysisResultAPI.API_RETRY_COUNT):
            try:
                response = requests.get(
                    url=result_uri,
                    headers={'x-pa-apikey': pa_context.api_key}
                )

                break

            except Exception as e:
                PackageAware.console_log(
                    "Analysis Result API Exception Occurred. "
                      "Attempt " + str(i + 1) + " of " + str(PackageAwareAnalysisResultAPI.API_RETRY_COUNT)
                )

        return response


class PackageAwareOnFailure:

    FAIL_THE_BUILD = "fail_the_build"
    CONTINUE_ON_FAILURE = "continue_on_failure"


class PackageAwareModeOfOperation:

    RUN_AND_WAIT = "run_and_wait"
    ASYNC_INIT = "async_init"
    ASYNC_RESULT = "async_result"


class PackageAwareAnalysisScript:

    MIN_ANALYSIS_RESULT_POLLING_INTERVAL = 10
    ASYNC_RESULT_FILE_NAME = "package_aware_async.json"
    PA_WORKSPACE_FOLDER = "package_aware/workspace"

    def __init__(self):

        self.code_root = PackageAware.get_current_directory()

        self.async_result_file = None

        self.mode = None
        self.on_failure = None

        self.directories_to_exclude = None
        self.files_to_exclude = None

        self.working_directory = None

        self.analysis_result_max_wait = None
        self.analysis_result_polling_interval = None

    def load_script_arguments(self):

        if args.mode is not None:
            self.mode = str(args.mode)
        else:
            self.mode = "run_and_wait"

        PackageAware.console_log("MODE: " + self.mode)

        if args.on_failure is not None:
            self.on_failure = str(args.on_failure)
        else:
            self.on_failure = "fail_the_build"

        PackageAware.console_log("ON_FAILURE: " + self.on_failure)

        self.directories_to_exclude = []
        temp_dirs_to_exclude = []
        if args.directories_to_exclude is not None and len(args.directories_to_exclude.strip()) > 0:
            PackageAware.console_log("DIRS_TO_EXCLUDE: " + args.directories_to_exclude.strip())
            temp_dirs_to_exclude = args.directories_to_exclude.split(",")

            for dir in temp_dirs_to_exclude:
                self.directories_to_exclude.append(self.code_root + dir)
        else:
            PackageAware.console_log("DIRS_TO_EXCLUDE: <NONE>")

        self.files_to_exclude = []
        temp_files_to_exclude = []
        if args.files_to_exclude is not None and len(args.files_to_exclude.strip()) > 0:
            PackageAware.console_log("FILES_TO_EXCLUDE: " + args.files_to_exclude.strip())
            temp_files_to_exclude = args.files_to_exclude.split(",")

            for a_file in temp_files_to_exclude:
                self.files_to_exclude.append(self.code_root + a_file)
        else:
            PackageAware.console_log("FILES_TO_EXCLUDE: <NONE>")

        # WORKING DIRECTORY & ASYNC RESUlT FILE
        if args.working_directory is not None:
            self.working_directory = args.working_directory.strip()
            if len(self.working_directory) > 0:

                # IS THIS LINUX OR WINDOWS?
                if self.working_directory.find("/") >= 0:

                    # Convert references to user home folder to absolute path
                    if self.working_directory.startswith("~/"):
                        home = str(Path.home())

                        if home.endswith("/"):
                            self.working_directory = home + self.working_directory[2:]
                        else:
                            self.working_directory = home + "/" + self.working_directory[2:]

                    if not self.working_directory.endswith("/"):
                        self.async_result_file = self.working_directory + "/" + PackageAwareAnalysisScript.PA_WORKSPACE_FOLDER + "/" + PackageAwareAnalysisScript.ASYNC_RESULT_FILE_NAME
                    else:
                        self.async_result_file = self.working_directory + PackageAwareAnalysisScript.PA_WORKSPACE_FOLDER + "/" + PackageAwareAnalysisScript.ASYNC_RESULT_FILE_NAME
                else:
                    if not self.working_directory.endswith("\\"):
                        self.async_result_file = self.working_directory + "\\" + PackageAwareAnalysisScript.ASYNC_RESULT_FILE_NAME

                    # Convert references to user home folder to absolute path
                    if self.working_directory.find("%userprofile%") >= 0:
                        home = str(Path.home())

                        if home.endswith("\\"):
                            self.working_directory = home + self.working_directory[2:]
                        else:
                            self.working_directory = home + "\\" + self.working_directory[2:]

                    if not self.working_directory.endswith("\\"):
                        self.async_result_file = self.working_directory + "\\" + PackageAwareAnalysisScript.PA_WORKSPACE_FOLDER + "\\" + PackageAwareAnalysisScript.ASYNC_RESULT_FILE_NAME
                    else:
                        self.async_result_file = self.working_directory + PackageAwareAnalysisScript.PA_WORKSPACE_FOLDER + "\\" + PackageAwareAnalysisScript.ASYNC_RESULT_FILE_NAME

        else:
            # FAllBACK - COULD RESULT IN ERROR DEPENDING ON MODE DESIRED
            self.working_directory = ""
            self.async_result_file = self.code_root + PackageAwareAnalysisScript.ASYNC_RESULT_FILE_NAME

        PackageAware.console_log("WORKING_DIRECTORY: " + self.working_directory)
        PackageAware.console_log("ASYNC_RESULT_FILE: " + self.async_result_file)

        # ANALYSIS RESULT MAX WAIT
        # Default: 300 (5 minutes)
        # Minimum: Any
        # Maximum: Unlimited
        analysis_result_max_wait = 5 * 60
        if args.analysis_result_max_wait is not None:
            self.analysis_result_max_wait = int(args.analysis_result_max_wait)

        PackageAware.console_log("ANALYSIS_RESULT_MAX_WAIT: " + str(self.analysis_result_max_wait))

        # ANALYSIS RESULT POLLING INTERVAL
        # Default: 10 seconds
        # Minimum: 10 seconds
        # Maximum: Unlimited
        self.analysis_result_polling_interval = 10
        if args.analysis_result_polling_interval is not None:
            self.analysis_result_polling_interval = int(args.analysis_result_polling_interval)
            if self.analysis_result_polling_interval < PackageAwareAnalysisScript.MIN_ANALYSIS_RESULT_POLLING_INTERVAL:
                self.analysis_result_polling_interval = PackageAwareAnalysisScript.MIN_ANALYSIS_RESULT_POLLING_INTERVAL

        PackageAware.console_log("ANALYSIS_RESULT_POLLING_INTERVAL: " + str(self.analysis_result_polling_interval))

    @staticmethod
    def register_arguments():

        parser = argparse.ArgumentParser(description="Package Aware CI Integration Script")

        # SCRIPT PARAMETERS

        parser.add_argument("-m", dest="mode",
                            help="Mode of operation: "
                                 "run_and_wait: Run Analysis & Wait ** Default Value, "
                                 "async_init: Async Init, "
                                 "async_result: Async Result",
                            type=str,
                            default="run_and_wait",
                            required=False
                            )

        parser.add_argument("-of", dest="on_failure",
                            help="On Failure: "
                                 "fail_the_build: Fail The Build ** Default Value, "
                                 "continue_on_failure: Continue On Failure",
                            type=str,
                            default="fail_the_build",
                            required=False
                            )

        parser.add_argument("-dte", dest="directories_to_exclude",
                            help="Listing of directories (relative to ./) to exclude from the search for manifest files.\n"
                                 "Example - Correct: bin/start/\n"
                                 "Example - Incorrect: ./bin/start/\n"
                                 "Example - Incorrect: /bin/start",
                            type=str,
                            required=False
                            )

        parser.add_argument("-fte", dest="files_to_exclude",
                            help="Listing of files (relative to ./) to exclude from the search for manifest files.\n"
                                 "Example - Correct: bin/start/requirements.txt\n"
                                 "Example - Incorrect: ./bin/start/requirements.txt\n"
                                 "Example - Incorrect: /bin/start/requirements.txt",
                            type=str,
                            required=False
                            )

        parser.add_argument("-wd", dest="working_directory",
                            help="Absolute path where Package Aware may write and read persistent files for the given build.\n"
                                 "Example - Correct: /tmp/workspace/\n"
                                 "Example - Incorrect: ./bin/start/\n"
                                 "Example - Incorrect: tmp/workspace",
                            type=str,
                            required=False
                            )

        parser.add_argument("-armw", dest="analysis_result_max_wait",
                            help="Maximum seconds to wait for Analysis Result. Default 300.",
                            type=int,
                            default=300,
                            required=False
                            )

        parser.add_argument("-arpi", dest="analysis_result_polling_interval",
                            help="Polling interval (in seconds) for analysis result completion (success/failure). "
                                 "Min value: 10",
                            type=int,
                            default=10,
                            required=False
                            )

        # CONTEXT PARAMETERS

        parser.add_argument("-buri", dest="base_uri",
                            help="API URI Path. Default Value: https://api.packageaware.io/api/",
                            type=str,
                            default="https://api.packageaware.io/api/",
                            required=False
                            )

        parser.add_argument("-scp", dest="source_code_path",
                            help="Root path to begin recursive search for manifests. Default Value: ./",
                            type=str,
                            default="./",
                            required=False
                            )

        parser.add_argument("-pn", dest="project_name",
                            help="Project name for tracking results",
                            type=str,
                            required=False
                            )

        parser.add_argument("-cid", dest="client_id",
                            help="API Client ID",
                            type=str,
                            required=False
                            )

        parser.add_argument("-akey", dest="api_key",
                            help="API Key",
                            type=str,
                            required=False
                            )

        return parser


if __name__ == "__main__":

    #if ((3, 0) <= sys.version_info <= (3, 9)):
    if sys.version_info < (3, 6):
        print("**** PACKAGE AWARE FATAL ERROR: Python Version 3.6 or higher is required ****")
        sys.exit(1)

    # Initialize Package Aware
    package_aware = PackageAware()

    # Register and load script arguments
    parser = package_aware.script.register_arguments()
    args = parser.parse_args()
    package_aware.script.load_script_arguments()

    if not package_aware.context.load(args):

        PackageAware.console_log("Could not find required Environment/Script Variables. "
                                 "One or more are missing or empty:")

        package_aware.context.print_invalid()

        if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
            sys.exit(1)
        else:
            sys.exit(0)

    # Ensure Working Directory is present if mode is ASYNC
    if package_aware.script.mode in(PackageAwareModeOfOperation.ASYNC_INIT, PackageAwareModeOfOperation.ASYNC_RESULT):
        if len(package_aware.script.working_directory) == 0:
            PackageAware.console_log("Working Directory is required when mode is ASYNC. Exiting.")
            if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
                sys.exit(1)
            else:
                sys.exit(0)

    if package_aware.script.mode in (PackageAwareModeOfOperation.RUN_AND_WAIT, PackageAwareModeOfOperation.ASYNC_INIT):

        # Make API call and store response
        structure_response = PackageAwareStructureAPI.exec(package_aware.context)

        if structure_response.original_response is None:
            PackageAware.console_log("A Structure API error occurred: Could not execute API.")
            if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
                sys.exit(1)
            else:
                sys.exit(0)

        if structure_response.original_response.status_code != 201:
            print("PACKAGE_AWARE: A Structure API error occurred: Response Code " +
                  str(structure_response.original_response.status_code)
            )
            if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
                sys.exit(1)
            else:
                sys.exit(0)

        # ## STRUCTURE API CALL SUCCESSFUL - CONTINUE

        PackageAware.console_log("------------------------")
        PackageAware.console_log("Analysis Structure Request Created")
        PackageAware.console_log("------------------------")
        PackageAware.console_log("Analysis Id: " + structure_response.analysis_id)
        PackageAware.console_log("Project Id:  " + structure_response.project_id)

        manifests_found_count = package_aware.send_manifests(
            structure_response.project_id,
            structure_response.analysis_id,
            package_aware.script.directories_to_exclude,
            package_aware.script.files_to_exclude
        )

        if manifests_found_count > 0:

            # api_start_url = package_aware.context.base_uri + \
            #                 "clients/" + package_aware.context.client_id + \
            #                 "/projects/" + project_id + \
            #                 "/analysis/" + analysis_id

            PackageAware.console_log("------------------------")
            PackageAware.console_log("Starting Analysis")
            PackageAware.console_log("------------------------")

            response = PackageAwareAnalysisStartAPI.exec(
                pa_context=package_aware.context,
                project_id=structure_response.project_id,
                analysis_id=structure_response.analysis_id
            )

            PackageAware.console_log("Analysis Start API Response Code: " + str(response.status_code))

            if response.status_code != 200:
                PackageAware.console_log("An error occurred: " + str(response.content))
                if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
                    sys.exit(1)
                else:
                    sys.exit(0)
            else:

                # NOTE: This is the only route where the initiate request was successful

                PackageAware.console_log(
                    "Analysis request is running, once completed, access the report using the links below"
                )
                PackageAware.console_log("ReportUrl: " + structure_response.report_url)
                PackageAware.console_log("EmbedUrl: " + structure_response.embed_url)

                if package_aware.script.mode == PackageAwareModeOfOperation.RUN_AND_WAIT:

                    package_aware.analysis_result_exec(
                        structure_response.report_status_url,
                        package_aware.script.analysis_result_max_wait,
                        package_aware.script.analysis_result_polling_interval
                    )

                elif package_aware.script.mode == PackageAwareModeOfOperation.ASYNC_INIT:

                    # Write file here for RESULT process to pick up when it runs later
                    file_contents = {"report_status_url": structure_response.report_status_url}
                    file = open(package_aware.script.async_result_file, "w")
                    file.write(json.dumps(file_contents))
                    file.close()

                    PackageAware.console_log("Write Analysis URL To File: " + package_aware.script.async_result_file)

                sys.exit(0)
        else:
            PackageAware.console_log("Could not locate any manifests under " + package_aware.context.source_code_path)
            if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
                sys.exit(1)
            else:
                sys.exit(0)

    elif package_aware.script.mode == PackageAwareModeOfOperation.ASYNC_RESULT:

        # Sit and wait for ASYNC RESULT

        try:

            with open(package_aware.script.async_result_file, 'r') as the_file:

                async_result_content = the_file.read()
                async_result_values = json.loads(async_result_content)

                package_aware.console_log("Getting Analysis Result For: " + async_result_values["report_status_url"])

                package_aware.analysis_result_exec(
                    async_result_values["report_status_url"],
                    package_aware.script.analysis_result_max_wait,
                    package_aware.script.analysis_result_polling_interval
                )

            sys.exit(0)

        except FileNotFoundError as e:
            PackageAware.console_log("ERROR: The async file (containing the report URL) could not be found. Exiting.")
            if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
                sys.exit(1)
            else:
                sys.exit(0)
    else:

        PackageAware.console_log("ERROR: Mode argument is not a valid Package Aware Mode.")

        if package_aware.script.on_failure == PackageAwareOnFailure.FAIL_THE_BUILD:
            sys.exit(1)
        else:
            sys.exit(0)

