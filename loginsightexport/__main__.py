import argparse
import collections
import logging
import netrc
import os
import shutil
import sys
import warnings
from datetime import datetime
from getpass import getpass, getuser

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.structures import CaseInsensitiveDict


from loginsightexport.binfit import merge, patch_bins_at_boundaries, split, sorted_by_startTimeMillis
from loginsightexport.compat import urlparse
from loginsightexport.paramhelper import ExplorerUrlParse, SeenWarning
from loginsightexport.progress import ProgressRange, ProgressBar
from loginsightexport.shorturl import unfurl_short_url
from loginsightexport.uidriver import Connection, Credentials, AggregateQuery, TechPreviewWarning
from loginsightexport.files import ExportBinToFile, InconsistentFile, FileNotFoundError


def arguments():
    # Try to discover the window size, so argparse can draw appropriately-wrapped help.
    os.environ['COLUMNS'] = str(min([120, shutil.get_terminal_size().columns]))

    parser = argparse.ArgumentParser(
        description="Export events from a VMware vRealize Log Insight server, write to local files",
        usage='%(prog)s https://loginsight/s/e6jc6n',
        epilog="asdf")

    parser.add_argument("url",
                        metavar='https://.../s/e6jc6n',
                        help="A short share URL, produced by the Log Insight UI.")
    parser.add_argument('-o', '--output',
                        # ="output",
                        default=os.getcwd(),
                        metavar="DIR",
                        help="Write exported data to this directory. Defaults to current: %(default)s")
    accountgroup = parser.add_argument_group("Account")
    accountgroup.add_argument("--username", help="Login with this username."
                                                 "If unspecified, try to retrieve credentials from .netrc file or shell or prompt. "
                                                 # "Active Directory accounts can be user, user@domain or DOMAIN\\user - "
                                                 # "See https://kb.vmware.com/kb/2069086"
                              )
    accountgroup.add_argument("--provider", default="Local", choices=['local', 'ad'],
                              help="Username originates from this identity provider. Default: %(default)s")
    accountgroup.add_argument("--netrc",
                              default=os.path.join(os.environ['HOME'], ".netrc"),
                              help="Alternate .netrc configuration file with credentials in the format "
                                   "`machine li.example.com login Charlie password SuperSecr3t! account Local`")

    certgroup = parser.add_argument_group("Certificates")
    certgroup.add_argument("--save", metavar="foo.pem",
                           help="Save the remote's certificate as a PEM-formatted file.")
    certgroup.add_argument("--verify", metavar="foo.pem", default=True,
                           help="Trust a remote's certificate if it matches this file.")
    certgroup.add_argument("--insecure", action="store_false", default=True, dest="verify",
                           help="Let someone MITM your HTTTPS connection.")

    loggroup = parser.add_argument_group("Display")
    loggroup.add_argument("-q", "--quiet", action="store_const", const=1, default=0, help="Silence progressbar.")
    loggroup.add_argument("-v", "--verbose", action="count", default=0, dest="loglevel", help="Replace progressbar with logs. -vv writes PII (urls & queries) to stdout")
    loggroup.add_argument("--noprompt", action="store_false", default=True, dest="prompt", help="Don't prompt for anything interactively")

    parser.add_argument("--nice", type=int, default=0, dest="delay", help="Be nice: delay seconds between chunk downloads.")
    parser.add_argument("--max", type=int, default=2000, help="Largest quantity of messages to retrieve in a single bin [1-20k], default %(default)s")
    parser.add_argument("--raw", dest="format", action="store_const", default="JSON", const="RAW", help="Export in %(const)s format instead of the %(default)s default")

    args = parser.parse_args()

    # Add hostname/port/username/password to args namespace, derived from URL or .netrc file
    remote = urlparse(args.url)

    args.hostname = remote.hostname
    args.port = remote.port if remote.port else 443
    args.password = None

    if args.save:
        pem = requests.packages.urllib3.util.ssl_.ssl.get_server_certificate((args.hostname, args.port))
        with open(args.save, 'x') as f:
            f.write(pem)
        if not args.quiet:
            print("Wrote PEM file {0!r}:".format(args.save))
            print(pem)
            parser.exit(2, ("Use it by invoking: " + parser.usage + " --verify %(filename)s\n") % dict(prog=parser.prog, filename=args.save))
        else:
            parser.exit(2)

    if args.username is None and remote.username is not None:
        args.username = remote.username

    if args.username is None:
        n = netrc.netrc(args.netrc)
        netrcline = n.authenticators(args.hostname)
        try:
            (args.username, args.provider, args.password) = netrcline
        except TypeError:
            pass  # Cannot parse netrc line (netrcline=None)
        del n

    if args.username is None and args.prompt:
        args.username = getuser()
        if args.username == "":
            args.username = None

    if args.username is None:
        parser.error(
            "Username required, either on command line or in ~/.netrc:\n"
            " * On the command line: --username=foo\n"
            " * As part of the URL: https://username@li.example.com\n"
            " * In a .netrc file: machine li.example.com login Charlie password SuperSecr3t! account Local"
        )

    if args.password is None and args.prompt:
        print("No password found for {0}@{1} in .netrc".format(args.username, args.hostname))
        try:
            args.password = getpass()
            if args.password == "":
                args.password = None
        except KeyboardInterrupt:
            print()
            sys.exit(130)  # Ctrl+C

    if args.password is None:
        parser.error(
            "Password required, either interactively or in ~/.netrc:\n"
            " * In a .netrc file: machine li.example.com login Charlie password SuperSecr3t! account Local"
        )

    if not os.path.isdir(args.output):
        parser.error("{0} is not a directory".format(args.output))

    nice_provider_names = CaseInsensitiveDict({'local': "DEFAULT", 'ad': "ACTIVE_DIRECTORY"})
    if args.provider in nice_provider_names:
        args.provider = nice_provider_names[args.provider]

    # Suppress warnings
    args.loglevel -= args.quiet

    args.path = remote.path
    args.query = remote.query

    return parser, args


def setup_logger(args):
    warnings.filterwarnings("ignore", category=TechPreviewWarning)
    warnings.filterwarnings("ignore", category=SeenWarning)

    # Set up logging according to command-line verbosity
    logger = logging.getLogger()
    logger.setLevel(int(30 - (args.loglevel * 10)))
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Set logging level to {0}".format(logging.getLevelName(logger.getEffectiveLevel())))

    # If log level is reduced, disable emissions from the `warnings` module; aka the
    if not logger.isEnabledFor(logging.WARNING):
        warnings.simplefilter("ignore")

    return logger


def main():
    parser, args = arguments()
    logger = setup_logger(args)

    with ProgressBar([], quiet=True) as app:
        session = requests.Session()

        retries = Retry(total=20, backoff_factor=1, status_forcelist=[500, 502, 503, 504])  # Retry on server errors
        session.mount('https://', HTTPAdapter(max_retries=retries))

        auth = Credentials(args.username, args.password, args.provider, reuse_session=session)
        ui = Connection(args.hostname, port=args.port, verify=args.verify, auth=auth, existing_session=session)

        try:
            ui.ping()  # Make a GET / request to the server.
        except requests.exceptions.SSLError as e:
            logger.info("SSLError", exc_info=e)
            parser.error(("The remote SSL certificate isn't trusted: {e}\n"
                          "Either add the certificate to your system's trust store or "
                          "save the certificate to a file with `{prog} --save/--verify foo.pem`.\n"
                          "If you want to view the certificate text, use "
                          "`openssl s_client -showcerts -connect {a.hostname}:{a.port} -CAfile foo.pem < /dev/null | openssl x509 -text -noout`"
                          ).format(prog=parser.prog, e=e, a=args))
        except Exception as e:
            logger.info("SSLError", exc_info=e)
            print("Failed to connect to remote server: {0}".format(e))
            parser.exit()

        version = ui.get("/api/v1/version").json()['version']
        logger.info("Connected to {0} running Log Insight {1}".format(args.hostname, version))
        ui.log("Connected")

        # If we got a short url, expand it to a long /explorer? one
        explorer_url = "%s?%s" % (args.path, args.query)
        logger.info("Exporting {0}".format(explorer_url))
        if explorer_url.startswith("/s/"):
            explorer_url = unfurl_short_url(ui, explorer_url)

        # Generate an initial list of binned timestamps
        root = ExplorerUrlParse(explorer_url)

        # We're ready to start doing work

        # Recursively split into smaller bins, with progress bar
        with ProgressRange() as callback:
            def retrieve_aggregate_results(bin=(None, None, None), report_callback=True):
                if report_callback:
                    callback.update([(bin[0], bin[1], 0)])
                a = AggregateQuery(ui, root.chartingurl_export(altstart=bin[0], altend=bin[1]))
                return sorted_by_startTimeMillis(patch_bins_at_boundaries(bin, a.bins))

            overview = retrieve_aggregate_results((root.start, root.end, 0), False)
            callback.start(overview)
            expanded_bins = list(split(overview, retrieve_aggregate_results, maximum=args.max))

            ui.log("Estimation over range {d}: {e} events in {b} bins took {r} requests".format(
                d=datetime.fromtimestamp(callback._end / 1000) - datetime.fromtimestamp(callback._start / 1000),
                e=sum([x[2] for x in expanded_bins]),
                b=len(expanded_bins),
                r=callback.updates,
            ))

            rendered_bins = list(merge(expanded_bins, maximum=args.max))

            ui.log("Repacked estimation over range {d}: {e} events in {b} bins".format(
                d=datetime.fromtimestamp(callback._end / float(1000)) - datetime.fromtimestamp(callback._start / float(1000)),
                e=sum([x[2] for x in rendered_bins]),
                b=len(rendered_bins),
            ))

        # Sanity check the proposed query plan
        # Bins are not evenly time-sized. Contigous bins under the maximum value-size limit have been merged.
        # [-999-][--900--] [80]  [1]  [-5-] [-900---]
        def assert_only(bin):
            raise RuntimeError("BUG: Unsplit buckets still exceed maximum %d" % args.max)
        list(split(rendered_bins, assert_only, maximum=args.max))

        total_bins = len(rendered_bins)
        if len(rendered_bins) == 0:
            parser.error("There appears to be no data in this query & time-range. Aborting.")

        # Sanity check output directory for filename collsions
        PREFIX = "output."
        expected_files = [PREFIX + "%s" % b[0] for b in rendered_bins]
        extra_files = [f for f in os.listdir(args.output) if f.startswith(PREFIX) and f not in expected_files]
        if extra_files:
            parser.error(
                "There are extra files in the output directory {output} which are not part of the desired output set {prefix}*. "
                "Delete them or use a different output directory:\n{extra_files}".format(
                    output=args.output,
                    prefix=PREFIX,
                    extra_files=" ".join(extra_files)
                ))

        stats = collections.Counter()
        try:
            with ProgressBar(rendered_bins,
                             suffix="files",
                             quiet=not logger.isEnabledFor(logging.WARNING),
                             log=logger.isEnabledFor(logging.INFO),
                             extra=stats) as iterable:
                for b in iterable:
                    export_file = ExportBinToFile(root, bin=b, output_directory=args.output, output_format=args.format, connection=ui)

                    try:
                        if export_file.valid:  # raises exceptions FileNotFoundError, InconsistentFile
                            export_file.logger.info("Already been retrieved, skipping.")
                            stats['skipped'] += 1
                            continue
                    except FileNotFoundError:
                        pass  # download this

                    downloaded_bytes = export_file.download()
                    stats['bytes'] += downloaded_bytes
                    export_file.logger.info("Wrote {bytes} bytes in {duration}".format(bytes=downloaded_bytes, duration=iterable.duration))

                    try:
                        if not export_file.valid:  # raises exceptions FileNotFoundError, InconsistentFile
                            raise InconsistentFile("Wrote inconsistent output file {f!r}.".format(f=export_file.filename))
                    except InconsistentFile:
                        raise

            # end with
        except InconsistentFile as e:
            parser.exit(status=65, message="%s - Delete it and retry, or report a bug.\n" % str(e))

        except FileExistsError as e:
            parser.exit(status=74, message="Refusing to overwrite existing unparsable file {f!r}. Delete it and retry, or report a bug.\n".format(f=e.filename))

    success_msg = "Complete export: {i.current} bins downloaded {s[bytes]} bytes in {i.duration} ({s[skipped]} already present)".format(s=stats, i=iterable)
    ui.log(success_msg)
    if logger.isEnabledFor(logging.WARNING) and not logger.isEnabledFor(logging.INFO):
        parser.exit(status=0, message="%s\n" % success_msg)


if __name__ == '__main__':
    main()
