import json
import os
from datetime import datetime

from bson import Int64
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.mongo_utils import get_mongo_connection_handle
from ebi_eva_internal_pyutils.pg_utils import execute_query, get_all_results_for_query

from utils.docker_utils import run_command_in_container
from utils.test_with_docker_compose import TestWithDockerCompose, log_on_failure

resources_dir = os.path.join(TestWithDockerCompose.resources_directory, 'release_automation')
maven_settings_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'maven-settings.xml')
maven_profile = 'localhost'

class TestRunReleaseForSpecies(TestWithDockerCompose):

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-release-automation.yml')
    container_name = 'eva_release_automation_test'
    container_release_dir = '/opt/test_eva_release'
    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_release_automation_test_run')
    container_log_files = []

    def setUp(self):
        super().setUp()
        self._add_data_to_docker()

    def tearDown(self):
        # Remove from within Docker to ensure we have permission
        try:
            run_command_in_container(self.container_name, f'rm -rf {self.container_release_dir}/*')
        except Exception:
            pass
        super().tearDown()

    def _add_data_to_docker(self):
        inventory_table = 'eva_progress_tracker.clustering_release_tracker'
        # Paths inside the executor Docker container (read-only volume mount)
        fasta_file = '/opt/tests/release_automation/resources/GCA_000005425.2.fa'
        report_file = '/opt/tests/release_automation/resources/GCA_000005425.2_assembly_report.txt'

        with get_metadata_connection_handle(maven_profile, maven_settings_file) as conn:
            insert_query = (
                f"insert into {inventory_table} "
                f"(taxonomy, scientific_name, assembly_accession, release_version, sources, fasta_path, "
                f"report_path, should_be_released, num_rs_to_release, total_num_variants, release_folder_name) "
                f"values (4530, 'Oryza sativa', 'GCA_000005425.2', 1, 'EVA', '{fasta_file}', "
                f"'{report_file}', True, 1, 1, 'oryza_sativa')"
            )
            execute_query(conn, insert_query)

        sves = read_mongo_data(os.path.join(resources_dir, 'submittedVariantEntities.json'))
        cves = read_mongo_data(os.path.join(resources_dir, 'clusteredVariantEntities.json'))
        svoe = read_mongo_data(os.path.join(resources_dir, 'submittedVariantOperationEntities.json'))
        cvoe = read_mongo_data(os.path.join(resources_dir, 'clusteredVariantOperationEntities.json'))

        with get_mongo_connection_handle(maven_profile, maven_settings_file) as mongo_handle:
            db = mongo_handle['eva_accession_sharded']
            db['dbsnpSubmittedVariantEntity'].insert_many(sves)
            db['dbsnpClusteredVariantEntity'].insert_many(cves)
            db['dbsnpSubmittedVariantOperationEntity'].insert_many(svoe)
            db['dbsnpClusteredVariantOperationEntity'].insert_many(cvoe)

    @log_on_failure
    def test_run_release_for_species(self):
        # Check pending status
        output = run_command_in_container(
            self.container_name,
            'python3 -m release_automation.run_release_for_species --list_status Pending'
        )
        expected_pending = (
            '| taxonomy | assembly_accession | release_version | release_status |\n'
            '|     4530 |    GCA_000005425.2 |               1 |        Pending |\n'
        )
        assert expected_pending == output

        # Run the release
        run_command_in_container(
            self.container_name,
            'python3 -m release_automation.run_release_for_species '
            '--taxonomy_id 4530 --assembly_accessions GCA_000005425.2 --release_version 1'
        )

        output_directory = os.path.join(self.test_run_dir, 'release_1')
        expected_files = [
            os.path.join(output_directory, 'oryza_sativa', 'GCA_000005425.2', f)
            for f in [
                'log_files/release_active_rs_4530_GCA_000005425.2_1.log',
                '4530_GCA_000005425.2_current_ids.vcf.gz',
                '4530_GCA_000005425.2_deprecated_ids.txt.gz',
                '4530_GCA_000005425.2_merged_ids.vcf.gz',
                'README_rs_ids_counts.txt',
            ]
        ]
        # Check output files exist on host (via volume mount)
        for expected_file in expected_files:
            assert os.path.isfile(expected_file), f'Expected file not found: {expected_file}'

        # Check counts
        count_file = expected_files[-1]
        counts = {}
        with open(count_file) as open_file:
            for line in open_file:
                sp_line = line.strip().split()
                if sp_line:
                    counts[sp_line[0]] = sp_line[1]
        assert counts == {
            '4530_GCA_000005425.2_current_ids.vcf.gz': '6',
            '4530_GCA_000005425.2_deprecated_ids.txt.gz': '1',
            '4530_GCA_000005425.2_merged_ids.vcf.gz': '1',
        }

        # Check completed status
        output = run_command_in_container(
            self.container_name,
            'python3 -m release_automation.run_release_for_species --list_status Completed'
        )
        expected_completed = (
            '| taxonomy | assembly_accession | release_version | release_status |\n'
            '|     4530 |    GCA_000005425.2 |               1 |      Completed |\n'
        )
        assert expected_completed == output

    @log_on_failure
    def test_publish_release_to_ftp(self):
        # Run the release to generate release files
        run_command_in_container(
            self.container_name,
            'python3 -m release_automation.run_release_for_species '
            '--taxonomy_id 4530 --assembly_accessions GCA_000005425.2 --release_version 1'
        )

        # Publish the release to the FTP folder
        run_command_in_container(
            self.container_name,
            'python3 -m publish_release_to_ftp.publish_release_files_to_ftp '
            '--release_version 1 --taxonomy_id 4530'
        )

        ftp_release_dir = os.path.join(self.test_run_dir, 'ftp', 'release_1')
        species_assembly_dir = os.path.join(ftp_release_dir, 'by_species', 'oryza_sativa', 'GCA_000005425.2')
        expected_files = [
            os.path.join(species_assembly_dir, f)
            for f in [
                '4530_GCA_000005425.2_current_ids.vcf.gz',
                '4530_GCA_000005425.2_current_ids.vcf.gz.csi',
                '4530_GCA_000005425.2_deprecated_ids.txt.gz',
                '4530_GCA_000005425.2_merged_ids.vcf.gz',
                '4530_GCA_000005425.2_merged_ids.vcf.gz.csi',
                'md5checksums.txt',
                'README_release_known_issues.txt',
                'README_release_general_info.txt',
                'README_rs_ids_counts.txt'
            ]
        ]
        for expected_file in expected_files:
            assert os.path.isfile(expected_file), f'Expected file not found: {expected_file}'

        assembly_dir = os.path.join(ftp_release_dir, 'by_assembly', 'GCA_000005425.2')
        assert os.path.isdir(assembly_dir), f'Expected assembly directory not found: {assembly_dir}'

    @log_on_failure
    def test_create_release_tracking_table(self):
        with get_metadata_connection_handle(maven_profile, maven_settings_file) as conn:
            # Insert a clustered_variant_update entry so fill_should_be_released picks it up
            execute_query(conn,
                "insert into evapro.clustered_variant_update "
                "(clustered_update_id, taxonomy_id, assembly_accession, source, ingestion_time) "
                "values (1, 4530, 'GCA_000005425.2', 'EVA', now())"
            )

        # Use version 1 (inserted by setUp) as the previous release to create version 2
        run_command_in_container(
            self.container_name,
            'python3 -m release_automation.create_release_tracking_table --release-version 2'
        )

        with get_metadata_connection_handle(maven_profile, maven_settings_file) as conn:
            results = get_all_results_for_query(
                conn,
                "select should_be_released from eva_progress_tracker.clustering_release_tracker "
                "where taxonomy=4530 and assembly_accession='GCA_000005425.2' and release_version=2"
            )
        assert len(results) == 1, f'Expected 1 result, got {len(results)}'
        assert results[0][0] is True, f'Expected should_be_released=True, got {results[0][0]}'


def read_mongo_data(json_file):
    with open(json_file) as open_file:
        json_data = json.load(open_file)
    for document in json_data:
        add_mongo_types(document)
        if 'inactiveObjects' in document:
            for sub_doc in document['inactiveObjects']:
                add_mongo_types(sub_doc)
    return json_data


def add_mongo_types(json_dict):
    for key in json_dict:
        if key in ['start', 'rs', 'accession', 'mergeInto']:
            json_dict[key] = Int64(json_dict[key])
        if key in ['createdDate']:
            json_dict[key] = datetime.strptime(json_dict[key], '%Y-%m-%dT%H:%M:%S.%fZ')
