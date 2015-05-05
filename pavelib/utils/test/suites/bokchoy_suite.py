"""
Class used for defining and running Bok Choy acceptance test suite
"""
import time

from paver.easy import sh
from pavelib.utils.test.suites import TestSuite
from pavelib.utils.envs import Env
from pavelib.utils.test import bokchoy_utils
from pavelib.utils.test import utils as test_utils

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text  # pylint: disable-msg=invalid-name

__test__ = False  # do not collect


class BokChoyTestSuite(TestSuite):
    """
    TestSuite for running Bok Choy tests
    Properties (below is a subset):
      test_dir - parent directory for tests
      log_dir - directory for test output
      report_dir - directory for reports (e.g., coverage) related to test execution
      xunit_report - directory for xunit-style output (xml)
      fasttest - when set, skip various set-up tasks (e.g., DB migrations)
      test_spec - when set, specifies test files, classes, cases, etc. See platform doc.
      default_store - modulestore to use when running tests (split or draft)
    """
    def __init__(self, *args, **kwargs):
        super(BokChoyTestSuite, self).__init__(*args, **kwargs)
        self.test_dir = Env.BOK_CHOY_DIR / kwargs.get('test_dir', 'tests')
        self.log_dir = Env.BOK_CHOY_LOG_DIR
        self.report_dir = Env.BOK_CHOY_REPORT_DIR
        self.xunit_report = self.report_dir / "xunit.xml"
        self.cache = Env.BOK_CHOY_CACHE
        self.fasttest = kwargs.get('fasttest', False)
        self.test_spec = kwargs.get('test_spec', None)
        self.default_store = kwargs.get('default_store', None)
        self.verbosity = kwargs.get('verbosity', 2)
        self.extra_args = kwargs.get('extra_args', '')
        self.har_dir = self.log_dir / 'hars'
        self.imports_dir = kwargs.get('imports_dir', None)
        self.external_services = kwargs.get('external_services', None)

    def __enter__(self):
        super(BokChoyTestSuite, self).__enter__()

        # Ensure that we have a directory to put logs and reports
        self.log_dir.makedirs_p()
        self.har_dir.makedirs_p()
        self.report_dir.makedirs_p()
        test_utils.clean_reports_dir()

        if not self.skip_clean:
            test_utils.clean_test_files()

        msg = colorize('green', "Checking for mongo, memchache, and mysql...")
        print(msg)
        bokchoy_utils.check_services()

        sh("{}/scripts/reset-test-db.sh".format(Env.REPO_ROOT))

        if not self.fasttest:
            # Process assets and set up database for bok-choy tests
            # Reset the database

            # Collect static assets
            sh("paver update_assets --settings=bok_choy")

        # Clear any test data already in Mongo or MySQLand invalidate
        # the cache
        bokchoy_utils.clear_mongo()
        self.cache.flush_all()

        sh(
            "DEFAULT_STORE={default_store}"
            " ./manage.py lms --settings bok_choy loaddata --traceback"
            " common/test/db_fixtures/*.json".format(
                default_store=self.default_store,
            )
        )

        if self.imports_dir:
            sh(
                "DEFAULT_STORE={default_store}"
                " ./manage.py cms --settings=bok_choy import {import_dir}".format(
                    default_store=self.default_store,
                    import_dir=self.imports_dir
                )
            )

        # Ensure the test servers are available
        msg = colorize('green', "Starting test servers...")
        print(msg)
        bokchoy_utils.start_servers(self.default_store, external_services=self.external_services)

        msg = colorize('green', "Waiting for servers to start...")
        print(msg)
        bokchoy_utils.wait_for_test_servers()

    def __exit__(self, exc_type, exc_value, traceback):
        super(BokChoyTestSuite, self).__exit__(exc_type, exc_value, traceback)

        msg = colorize('green', "Cleaning up databases...")
        print(msg)

        # Clean up data we created in the databases
        sh("./manage.py lms --settings bok_choy flush --traceback --noinput")
        bokchoy_utils.clear_mongo()

    @property
    def cmd(self):
        # Default to running all tests if no specific test is specified
        if not self.test_spec:
            test_spec = self.test_dir
        else:
            test_spec = self.test_dir / self.test_spec

        # Construct the nosetests command, specifying where to save
        # screenshots and XUnit XML reports
        cmd = [
            "DEFAULT_STORE={}".format(self.default_store),
            "SCREENSHOT_DIR='{}'".format(self.log_dir),
            "BOK_CHOY_HAR_DIR='{}'".format(self.har_dir),
            "SELENIUM_DRIVER_LOG_DIR='{}'".format(self.log_dir),
            "nosetests",
            test_spec,
            "--with-xunit",
            "--xunit-file={}".format(self.xunit_report),
            "--verbosity={}".format(self.verbosity),
        ]
        if self.pdb:
            cmd.append("--pdb")
        cmd.append(self.extra_args)

        cmd = (" ").join(cmd)
        return cmd


class BokChoyDevelopmentSuite(BokChoyTestSuite):

    def run_test(self):
        print('Run command:\n\n{0}\n\nPress Ctrl-C to exit...'.format(self.cmd))
        while True:
            time.sleep(10000)
