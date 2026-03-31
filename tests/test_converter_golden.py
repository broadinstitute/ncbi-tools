"""
Golden output tests for the Asymmetrik broad-tsv-converter.

These tests run the Node.js converter in test mode against known TSV inputs
and verify the XML output structure. The assertions are ported from the
Asymmetrik Mocha test suite (test/scripts/tsv-to-xml.js) and serve as
acceptance criteria for any future rewrite.

Prerequisites:
    - Node.js and the converter must be installed at /opt/converter
    - These tests are designed to run inside the Docker container

To run locally in the Docker container:
    docker run --rm -v $(pwd):/work ghcr.io/broadinstitute/ncbi-tools \
        bash -c "cd /work && python -m pytest tests/ -v"
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

CONVERTER_DIR = "/opt/converter"
TEST_DATA_DIR = Path(__file__).parent / "data"
MINIMAL_CONFIG = {
    "ftpConfig": {
        "host": "fakehost",
        "port": 22,
        "user": "fakeuser",
        "pass": "fakepass",
        "pollingInterval": 1,
    },
    "organizationConfig": {
        "name": "Gotham Institute",
        "type": "institute",
        "spuid_namespace": "InstituteNamespace",
        "contact": {"email": "batman@email.com"},
    },
}

# Skip all tests if the converter is not installed (e.g., running outside Docker)
pytestmark = pytest.mark.skipif(
    not os.path.isdir(CONVERTER_DIR),
    reason="Converter not installed (run inside Docker container)",
)


def write_config_js(config: dict, path: Path) -> None:
    """Write a config.js file from a Python dict."""
    lines = []
    if "ftpConfig" in config:
        lines.append(f"exports.ftpConfig = {json.dumps(config['ftpConfig'])};")
    if "organizationConfig" in config:
        lines.append(
            f"exports.organizationConfig = {json.dumps(config['organizationConfig'])};"
        )
    if "submitterConfig" in config:
        lines.append(
            f"exports.submitterConfig = {json.dumps(config['submitterConfig'])};"
        )
    path.write_text("\n".join(lines) + "\n")


def run_converter(tsv_filename: str, config: dict, extra_args: list[str] | None = None) -> ET.Element:
    """
    Run the converter in test mode and return parsed XML output.

    Copies the TSV into the converter's files/ directory, writes config,
    runs the converter, and parses the output XML.
    """
    extra_args = extra_args or []

    # Write config
    config_path = Path(CONVERTER_DIR) / "src" / "config.js"
    write_config_js(config, config_path)

    # Copy TSV input
    src_tsv = TEST_DATA_DIR / tsv_filename
    dest_tsv = Path(CONVERTER_DIR) / "files" / f"tests/{tsv_filename}"
    dest_tsv.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_tsv, dest_tsv)

    # Build command
    basename = tsv_filename.rsplit(".", 1)[0]
    cmd = [
        "node",
        "src/main.js",
        f"-i=tests/{tsv_filename}",
        "--force",
        "--runTestMode",
        "--debug",
    ] + extra_args

    # Run converter
    result = subprocess.run(
        cmd,
        cwd=CONVERTER_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Converter failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # Find and parse output XML
    output_xml = Path(CONVERTER_DIR) / "files" / f"tests/{basename}-submission.xml"
    if not output_xml.exists():
        # Try without the tests/ prefix
        output_xml = Path(CONVERTER_DIR) / "files" / f"{basename}-submission.xml"
    if not output_xml.exists():
        pytest.fail(
            f"Output XML not found. Files in converter/files/: "
            f"{list(Path(CONVERTER_DIR, 'files').rglob('*.xml'))}"
        )

    tree = ET.parse(output_xml)
    return tree.getroot()


# ---------------------------------------------------------------------------
# Helper functions for navigating XML
# ---------------------------------------------------------------------------

def find_text(elem: ET.Element, path: str) -> str:
    """Find element by path and return its text, or empty string."""
    found = elem.find(path)
    return (found.text or "") if found is not None else ""


def find_attr(elem: ET.Element, path: str, attr: str) -> str:
    """Find element by path and return an attribute value."""
    found = elem.find(path)
    return found.get(attr, "") if found is not None else ""


# ---------------------------------------------------------------------------
# BioSample conversion tests
# ---------------------------------------------------------------------------

class TestBioSampleConversion:
    """Tests ported from Asymmetrik test/scripts/tsv-to-xml.js BioSample tests."""

    def test_generates_submission_xml(self):
        """Should generate submission xml without errors."""
        root = run_converter("biosample-example.tsv", MINIMAL_CONFIG)
        assert root.tag == "Submission"

    def test_minimal_config_description(self):
        """Should successfully parse minimum required config."""
        root = run_converter("biosample-example.tsv", MINIMAL_CONFIG)

        # Test Description Block
        desc = root.find("Description")
        assert desc is not None

        software = desc.find("SubmissionSoftware")
        assert software is not None
        assert software.get("version") == "asymmetrik-tsv@1.0.0"

        org = desc.find("Organization")
        assert org is not None
        assert org.get("type") == "institute"
        assert find_text(org, "Name") == "Gotham Institute"
        assert find_attr(org, "Contact", "email") == "batman@email.com"

    def test_action_count(self):
        """Should have 3 Action blocks (one per TSV row)."""
        root = run_converter("biosample-example.tsv", MINIMAL_CONFIG)
        actions = root.findall("Action")
        assert len(actions) == 3

    def test_biosample_fields(self):
        """Should properly render AddData fields per row of the TSV file."""
        root = run_converter(
            "biosample-example.tsv",
            MINIMAL_CONFIG,
            ["-c=this is a fun comment!", "--releasedate=2017-01-01"],
        )
        actions = root.findall("Action")
        assert len(actions) == 3

        # First action
        action = actions[0]
        add_data = action.find("AddData")
        assert add_data is not None
        assert add_data.get("target_db") == "BioSample"

        # Identifier
        spuid = add_data.find("Identifier/SPUID")
        assert spuid is not None
        assert spuid.text == "name1"
        assert spuid.get("spuid_namespace") == "InstituteNamespace"

        # Data content
        assert add_data.find("Data").get("content_type") == "XML"

        biosample = add_data.find("Data/XmlContent/BioSample")
        assert biosample is not None
        assert biosample.get("schema_version") == "2.0"

        # SampleId
        sample_spuid = biosample.find("SampleId/SPUID")
        assert sample_spuid.text == "name1"
        assert sample_spuid.get("spuid_namespace") == "InstituteNamespace"

        # Organism
        organism = biosample.find("Organism")
        assert find_text(organism, "OrganismName") == "Severe acute respiratory syndrome coronavirus 2"
        assert find_text(organism, "IsolateName") == "SARS-CoV-2/Human/USA/MA-MGH-03863/2020"

        # BioProject
        assert find_text(biosample, "BioProject/PrimaryId") == "project-leona"

        # Package
        assert find_text(biosample, "Package") == "Pathogen.cl"

        # Attributes
        attributes = biosample.findall("Attributes/Attribute")
        attr_map = {a.get("attribute_name"): a.text for a in attributes}
        assert attr_map["isolate"] == "SARS-CoV-2/Human/USA/MA-MGH-03863/2020"
        assert attr_map["collected_by"] == "Massachusetts General Hospital"
        assert attr_map["collection_date"] == "5/26/2020"
        assert attr_map["geo_loc_name"] == "USA: Massachusetts"
        assert attr_map["isolation_source"] == "Clinical"
        assert attr_map["lat_lon"] == "missing"
        assert attr_map["host"] == "Homo sapiens"
        assert attr_map["host_disease"] == "COVID-19"
        assert attr_map["host_subject_id"] == "MA-MGH-03863"
        assert attr_map["anatomical_part"] == "Nasopharynx (NP)"
        assert attr_map["body_product"] == "Mucus"
        assert attr_map["purpose_of_sampling"] == "Diagnostic Testing"
        assert attr_map["purpose_of_sequencing"] == "Longitudinal surveillance (repeat sampling)"

    def test_comment_and_release_date(self):
        """Should append command line properties (releaseDate, comments)."""
        root = run_converter(
            "biosample-example.tsv",
            MINIMAL_CONFIG,
            ["-c=this is a fun comment!", "--releasedate=2017-01-01"],
        )
        desc = root.find("Description")
        assert find_text(desc, "Comment") == "this is a fun comment!"
        assert find_attr(desc, "Hold", "release_date") == "2017-01-01"

    def test_extra_organization_info(self):
        """Should include extra organization information if provided."""
        config = {
            "organizationConfig": {
                "name": "Gotham Institute",
                "type": "institute",
                "spuid_namespace": "InstituteNamespace",
                "contact": {"email": "batman@email.com"},
                "role": "owner",
                "org_id": 123,
                "group_id": "group_id",
                "url": "url",
                "address": {
                    "department": "Department of Villains",
                    "institution": "Gotham Institute",
                    "street": "123 fake street",
                    "city": "Gotham",
                    "state": "Metropolis",
                    "country": "USA",
                    "postal_code": 12333,
                },
            }
        }
        root = run_converter("biosample-example.tsv", config)
        org = root.find("Description/Organization")

        assert org.get("role") == "owner"
        assert org.get("org_id") == "123"
        assert org.get("group_id") == "group_id"
        assert org.get("url") == "url"

        addr = org.find("Address")
        assert addr.get("postal_code") == "12333"
        assert find_text(addr, "Department") == "Department of Villains"
        assert find_text(addr, "Institution") == "Gotham Institute"
        assert find_text(addr, "Street") == "123 fake street"
        assert find_text(addr, "City") == "Gotham"
        assert find_text(addr, "Sub") == "Metropolis"
        assert find_text(addr, "Country") == "USA"

    def test_submitter_info(self):
        """Should include submitter information if provided."""
        config = {
            "organizationConfig": {
                "name": "Gotham Institute",
                "type": "institute",
                "spuid_namespace": "InstituteNamespace",
                "contact": {"email": "batman@email.com"},
            },
            "submitterConfig": {
                "account_id": "accountId",
                "contact": {"email": "test@email.com"},
            },
        }
        root = run_converter("biosample-example.tsv", config)
        submitter = root.find("Description/Submitter")
        assert submitter is not None
        assert submitter.get("account_id") == "accountId"
        assert find_attr(submitter, "Contact", "email") == "test@email.com"


# ---------------------------------------------------------------------------
# SRA conversion tests
# ---------------------------------------------------------------------------

class TestSRAConversion:
    """Tests ported from Asymmetrik test/scripts/tsv-to-xml.js SRA tests."""

    def test_sra_basic(self):
        """Should be able to process SRA files."""
        root = run_converter(
            "sra-example.tsv",
            MINIMAL_CONFIG,
            [
                "--submissionType=sra",
                "--bioproject=fakebioproject",
                "submissionFileLoc=gs://",
            ],
        )
        actions = root.findall("Action")
        action = actions[0]
        add_files = action.find("AddFiles")

        assert add_files.get("target_db") == "SRA"

        spuid = add_files.find("Identifier/SPUID")
        assert spuid.text == "USA-CT-CDCBI-CRSP_KHN4JH3NU426HHDE-2021.l21R-118CR0484_000001321513"
        assert spuid.get("spuid_namespace") == "InstituteNamespace"

        attr_refs = add_files.findall("AttributeRefId")
        assert len(attr_refs) == 2
        assert attr_refs[0].get("name") == "BioProject"
        assert find_text(attr_refs[0], "RefId/PrimaryId") == "fakebioproject"
        assert find_attr(attr_refs[0], "RefId/PrimaryId", "db") == "BioProject"
        assert attr_refs[1].get("name") == "BioSample"
        assert find_text(attr_refs[1], "RefId/PrimaryId") == "SAMN19077089"
        assert find_attr(attr_refs[1], "RefId/PrimaryId", "db") == "BioSample"

    def test_sra_single_file(self):
        """Should handle SRA TSV with single filename attribute."""
        root = run_converter(
            "sra-example.tsv",
            MINIMAL_CONFIG,
            ["--submissionType=sra", "--bioproject=fakebioproject"],
        )
        action = root.findall("Action")[0]
        files = action.findall("AddFiles/File")

        assert len(files) == 1
        assert files[0].get("cloud_url") == (
            "USA-CT-CDCBI-CRSP_KHN4JH3NU426HHDE-2021"
            ".l21R-118CR0484_000001321513.HC2GYDRXY.1.cleaned.bam"
        )
        assert find_text(files[0], "DataType") == "generic-data"

    def test_sra_multiple_files(self):
        """Should handle SRA TSV with multiple filename attributes."""
        root = run_converter(
            "sra-multifile-example.tsv",
            MINIMAL_CONFIG,
            ["--submissionType=sra", "--bioproject=fakebioproject"],
        )
        action = root.findall("Action")[0]
        files = action.findall("AddFiles/File")

        assert len(files) == 4
        assert files[0].get("cloud_url") == (
            "USA-MA-Broad_CRSP-00810-2021.l000013221203_H8.HMTLKAFX2.1.cleaned.bam"
        )
        assert files[1].get("cloud_url") == (
            "USA-MA-Broad_CRSP-00810-2021.l000013221203_H8.HMTLKAFX2.2.cleaned.bam"
        )
        assert files[2].get("cloud_url") == (
            "USA-MA-Broad_CRSP-00810-2021.l000013221203_H8.HMTLKAFX2.3.cleaned.bam"
        )
        assert files[3].get("cloud_url") == (
            "USA-MA-Broad_CRSP-00810-2021.l000013221203_H8.HMTLKAFX2.4.cleaned.bam"
        )

    def test_sra_submission_file_loc_prepend(self):
        """submissionFileLoc: should prepend the submission file location."""
        root = run_converter(
            "sra-example.tsv",
            MINIMAL_CONFIG,
            [
                "--submissionType=sra",
                "--bioproject=fakebioproject",
                "submissionFileLoc=gs://",
            ],
        )
        action = root.findall("Action")[0]
        files = action.findall("AddFiles/File")
        assert files[0].get("cloud_url") == (
            "gs://USA-CT-CDCBI-CRSP_KHN4JH3NU426HHDE-2021"
            ".l21R-118CR0484_000001321513.HC2GYDRXY.1.cleaned.bam"
        )

    def test_sra_submission_file_loc_slash(self):
        """submissionFileLoc: should add separating slash if missing."""
        root = run_converter(
            "sra-example.tsv",
            MINIMAL_CONFIG,
            [
                "--submissionType=sra",
                "--bioproject=fakebioproject",
                "submissionFileLoc=gs",
            ],
        )
        action = root.findall("Action")[0]
        files = action.findall("AddFiles/File")
        assert files[0].get("cloud_url") == (
            "gs/USA-CT-CDCBI-CRSP_KHN4JH3NU426HHDE-2021"
            ".l21R-118CR0484_000001321513.HC2GYDRXY.1.cleaned.bam"
        )

    def test_sra_multifile_with_loc(self):
        """submissionFileLoc: should render consistently across multiple files."""
        root = run_converter(
            "sra-multifile-example.tsv",
            MINIMAL_CONFIG,
            [
                "--submissionType=sra",
                "--bioproject=fakebioproject",
                "submissionFileLoc=boom",
            ],
        )
        action = root.findall("Action")[0]
        files = action.findall("AddFiles/File")
        assert files[0].get("cloud_url") == (
            "boom/USA-MA-Broad_CRSP-00810-2021.l000013221203_H8.HMTLKAFX2.1.cleaned.bam"
        )
        assert files[3].get("cloud_url") == (
            "boom/USA-MA-Broad_CRSP-00810-2021.l000013221203_H8.HMTLKAFX2.4.cleaned.bam"
        )


# ---------------------------------------------------------------------------
# Report parsing tests
# ---------------------------------------------------------------------------

class TestReportParsing:
    """Tests for parsing NCBI XML response reports."""

    def test_parse_report_status(self):
        """Should parse submission status from report XML."""
        report_xml = TEST_DATA_DIR / "sample-report.xml"
        tree = ET.parse(report_xml)
        root = tree.getroot()

        assert root.tag == "SubmissionStatus"
        assert root.get("status") == "processed-ok"

    def test_parse_report_actions(self):
        """Should extract action statuses from report."""
        report_xml = TEST_DATA_DIR / "sample-report.xml"
        tree = ET.parse(report_xml)
        root = tree.getroot()

        actions = root.findall("Action")
        assert len(actions) == 2

        for action in actions:
            assert action.get("status") == "processed-ok"
            assert action.get("target_db") == "BioSample"

    def test_parse_report_accessions(self):
        """Should extract accession numbers from report."""
        report_xml = TEST_DATA_DIR / "sample-report.xml"
        tree = ET.parse(report_xml)
        root = tree.getroot()

        actions = root.findall("Action")
        accessions = []
        for action in actions:
            obj = action.find("Response/Object")
            if obj is not None:
                accessions.append(obj.get("accession"))

        assert accessions == ["SAMN0000000", "SAMN0001234"]

    def test_parse_report_spuid(self):
        """Should extract SPUIDs from report for data mapping."""
        report_xml = TEST_DATA_DIR / "sample-report.xml"
        tree = ET.parse(report_xml)
        root = tree.getroot()

        actions = root.findall("Action")
        spuids = []
        for action in actions:
            obj = action.find("Response/Object")
            if obj is not None:
                spuids.append(obj.get("spuid"))

        assert spuids == ["ABC123", "ABC123"]

    def test_parse_report_messages(self):
        """Should extract messages from report."""
        report_xml = TEST_DATA_DIR / "sample-report.xml"
        tree = ET.parse(report_xml)
        root = tree.getroot()

        actions = root.findall("Action")
        for action in actions:
            msg = action.find("Response/Message")
            assert msg is not None
            assert msg.text == "Successfully loaded"
            assert msg.get("severity") == "info"
