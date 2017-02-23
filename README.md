A command-line exporter of log events in VMware vRealize Log Insight. Exceed the 20k UI limit. Write local files.

# loginsight-export

## Installation
1. Open a command prompt.
2. `pip install loginsight-export`
3. `loginsight-export -h`

## Usage
1. In Log Insight Interactive Analytics, perform a query of arbitrary complexity and size.
2. Use the ![](exportshare.png) Share button to generate a short url for the current query.
3. `loginsight-export https://loginsight.example.com/s/123456`

## Overview

[VMware vRealize Log Insight](https://vmware.com/go/loginsight/docs) supports exporting query results to a file in the UI. However, a single export is limited to 20k results. To export more results, an operator can execute a sequence of queries with non-overlapping time-ranges, each of which contained less than 20k. As scale increases, this becomes cumbersome. This utility starts with a single UI-driven time-range, recursively breaks the full range down into sequential <=20k-sized chunks, and executes an export for each chunk.

## Prerequisites

* Built on [Requests](http://python-requests.org/).
* Uses `tox`, `pytest`, `requests-mock` for testing.

## Contributing

The loginsight-export project team welcomes contributions from the community. If you wish to contribute code and you have not
signed our contributor license agreement (CLA), our bot will update the issue when you open a Pull Request. For any
questions about the CLA process, please refer to our [FAQ](https://cla.vmware.com/faq). For more detailed information,
refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Distributed under the Apache Version 2.0 license](LICENSE.txt)
